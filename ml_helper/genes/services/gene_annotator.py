import requests
import time
from typing import Optional, Dict, List
import re

from .translation import translate_protein_class, translate_biological_process, translate_molecular_function

class GeneAnnotator:
    MYGENE_URL = "http://mygene.info/v3/query"
    PROTEIN_ATLAS_BASE = "https://www.proteinatlas.org"
    
    # In-memory кэш
    _cache_ensembl = {}
    _cache_hpa = {}
    
    def __init__(self, timeout: int = 10, delay_between_requests: float = 0.3):
        self.timeout = timeout
        self.delay = delay_between_requests
    
    def _clean_symbol(self, symbol: str) -> str:
        if not symbol:
            return ""
        cleaned = re.sub(r'^\?\|\d+\s*', '', str(symbol).strip())
        cleaned = re.sub(r'[^A-Za-z0-9_-]', '', cleaned)
        return cleaned.upper()
    
    def _extract_ensembl_id(self, ensembl_data) -> Optional[str]:
        if not ensembl_data:
            return None
        if isinstance(ensembl_data, str):
            return ensembl_data
        if isinstance(ensembl_data, dict):
            return ensembl_data.get('gene') or ensembl_data.get('id')
        if isinstance(ensembl_data, list) and ensembl_data:
            return self._extract_ensembl_id(ensembl_data[0])
        return None
    
    def _parse_mygene_response(self, response_data) -> List[dict]:
        if isinstance(response_data, list):
            return response_data
        if isinstance(response_data, dict):
            return response_data.get('hits', [])
        return []
    
    def gene_symbol_to_ensembl(self, gene_symbols: List[str]) -> Dict[str, Optional[str]]:
        result = {}
        to_fetch = []
        
        for sym in gene_symbols:
            clean = self._clean_symbol(sym)
            if not clean:
                result[sym] = None
                continue
            if clean in self._cache_ensembl:
                result[sym] = self._cache_ensembl[clean]
            else:
                to_fetch.append(clean)
                result[sym] = None
                
        if to_fetch:
            try:
                response = requests.post(
                    self.MYGENE_URL,
                    data={
                        'q': ','.join(to_fetch),
                        'scopes': 'symbol',
                        'fields': 'ensembl.gene',
                        'species': 'human',
                        'size': 1000
                    },
                    headers={'content-type': 'application/x-www-form-urlencoded'},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                hits = self._parse_mygene_response(data)
                
                for item in hits:
                    symbol = item.get('symbol', item.get('query', '')).upper()
                    ensembl_data = item.get('ensembl')
                    ensembl_id = self._extract_ensembl_id(ensembl_data)
                    
                    self._cache_ensembl[symbol] = ensembl_id
                    
                    for orig in [k for k in result.keys() if self._clean_symbol(k) == symbol]:
                        result[orig] = ensembl_id
                        
            except Exception:
                pass
                
        return result
    
    def fetch_hpa_data(self, ensembl_id: str) -> Optional[dict]:
        if not ensembl_id:
            return None
        if ensembl_id in self._cache_hpa:
            return self._cache_hpa[ensembl_id]
            
        try:
            url = f"{self.PROTEIN_ATLAS_BASE}/{ensembl_id}.json"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 404:
                self._cache_hpa[ensembl_id] = None
                return None
                
            response.raise_for_status()
            data = response.json()
            self._cache_hpa[ensembl_id] = data
            return data
        except Exception:
            self._cache_hpa[ensembl_id] = None
            return None
    
    @staticmethod
    def _safe_join(value) -> Optional[str]:
        if isinstance(value, list):
            return ", ".join(str(v) for v in value if v)
        return str(value) if isinstance(value, (str, int, float)) and str(value).strip() else None
    
    def annotate_genes(self, gene_importance: Dict[str, float], top_n: int = 10) -> List[dict]:
        if not gene_importance:
            return []
            
        sorted_genes = sorted(gene_importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
        symbols = [g[0] for g in sorted_genes]
        
        ensembl_map = self.gene_symbol_to_ensembl(symbols)
        results = []
        
        for gene, importance in sorted_genes:
            ensembl_id = ensembl_map.get(gene)
            
            hpa_data = self.fetch_hpa_data(ensembl_id)
            protein_class = hpa_data.get("Protein class") if hpa_data else None
            
            results.append({
                "gene": gene,
                "importance": round(float(importance), 4),
                "ensembl_id": ensembl_id,
                "description": hpa_data.get("Gene description") if hpa_data else None,
                
                "protein_class": translate_protein_class(protein_class),
                "biological_process": translate_biological_process(
                    hpa_data.get("Biological process")
                ) if hpa_data else None,
                
                "molecular_function": translate_molecular_function(
                    hpa_data.get("Molecular function")
                ) if hpa_data else None,

                "cancer_related": (
                    "Cancer-related genes" in (protein_class or [])
                    if isinstance(protein_class, (list, tuple)) else False
                ),
            })
            
            time.sleep(self.delay)
            
        return results

import os
import joblib
import pandas as pd
import numpy as np
import warnings
from catboost import CatBoostClassifier, Pool

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "catboost_model.cbm")
FEATURES_PATH = os.path.join(BASE_DIR, "feature_names.pkl")
SELECTOR_PATH = os.path.join(BASE_DIR, "selector.pkl")

model = CatBoostClassifier()
model.load_model(MODEL_PATH)

with open(FEATURES_PATH, "rb") as f:
    feature_names = joblib.load(f)

selector = joblib.load(SELECTOR_PATH)

def _map_to_original_names(importance_array: np.ndarray) -> dict:
    n_original = len(feature_names)
    full_imp = np.zeros(n_original)
    
    if hasattr(selector, 'get_support'):
        mask = selector.get_support()
        n_selected = np.sum(mask)
        if len(importance_array) == n_selected:
            full_imp[mask] = importance_array
        else:
            print(f"Размер не совпадает: importance={len(importance_array)}, selected={n_selected}")
            #выравнивание
            full_imp[:min(len(importance_array), n_selected)] = importance_array[:n_selected]
    else:
        full_imp[:len(importance_array)] = importance_array
        
    return {name: float(val) for name, val in zip(feature_names, full_imp) if val > 1e-6}

def predict_from_dataframe(df: pd.DataFrame):
    
    try:
        #Выравнивание колонок
        df_aligned = df.reindex(columns=feature_names, fill_value=0)
        print(f"После reindex: {df_aligned.shape[0]}×{df_aligned.shape[1]}")
        
        #Применяем селектор
        df_selected = selector.transform(df_aligned)
        print(f"После selector: {df_selected.shape[0]}×{df_selected.shape[1]}")
        
        #Предсказание
        preds = model.predict(df_selected)
        probas = model.predict_proba(df_selected)
        classes = model.classes_
        
        results = []
        for i in range(len(preds)):
            raw_pred = preds[i]
            label = str(raw_pred.item()) if hasattr(raw_pred, 'item') else str(raw_pred[0] if isinstance(raw_pred, (list, np.ndarray)) else raw_pred)
            
            all_probs = [
                {"label": str(classes[j]), "probability": round(probas[i][j] * 100, 2)}
                for j in range(len(classes))
            ]
            all_probs.sort(key=lambda x: x["probability"], reverse=True)
            
            results.append({
                "label": label,
                "probability": all_probs[0]["probability"],
                "alternatives": [p for p in all_probs[1:] if p["probability"] > 1.0]
            })
        
        gene_importance = {}
        try:            
            shap_vals = model.get_feature_importance(data=Pool(df_selected), type='ShapValues')
            shap_arr = np.asarray(shap_vals)
            
            for i in range(len(preds)):
                pred_class_idx = np.argmax(probas[i])
                
                if shap_arr.ndim == 3:
                    shap_raw = shap_arr[i, pred_class_idx, :-1]  # убираем bias-столбец
                elif shap_arr.ndim == 2:
                    shap_raw = shap_arr[i, :-1]
                else:
                    shap_raw = shap_arr[i]
                
                gene_imp_dict = _map_to_original_names(np.abs(shap_raw))
                top_10_genes = dict(sorted(gene_imp_dict.items(), key=lambda x: x[1], reverse=True)[:10])
                
                results[i]["top_genes"] = top_10_genes
                
            if results and "top_genes" in results[0]:
                gene_importance = results[0]["top_genes"]
            
        except Exception as e:
            try:
                cb_imp = model.get_feature_importance()
                gene_importance = _map_to_original_names(cb_imp)
            except Exception as e2:
                gene_importance = {}

        return results, gene_importance
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

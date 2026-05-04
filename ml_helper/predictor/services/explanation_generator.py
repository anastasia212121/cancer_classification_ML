class ExplanationGenerator:
    def generate(self, prediction: dict, genes: list) -> str:
        label = prediction.get("label", "неизвестно")
        prob = prediction.get("probability", 0)

        if not genes:
            base_text = f"Модель предсказала {label} с вероятностью {prob}%, однако данные о генах отсутствуют."
            return self._disclaimer(base_text)

        top_gene_names = [g["gene"] for g in genes[:3]]
        cancer_genes = [g["gene"] for g in genes if g.get("cancer_related")]

        processes = []
        for g in genes:
            if g.get("biological_process"):
                processes.extend([p.strip().lower() for p in g["biological_process"].split(",")])

        processes = list(set(processes))[:3]

        if prob >= 85:
            base_text = self._high_confidence(label, prob, top_gene_names, cancer_genes, processes)
        elif prob >= 60:
            base_text = self._medium_confidence(label, prob, top_gene_names, cancer_genes, processes)
        else:
            base_text = self._low_confidence(label, prob, top_gene_names, cancer_genes, processes)

        return self._disclaimer(base_text)

    def _high_confidence(self, label, prob, genes, cancer_genes, processes):
        text = (
            f"Модель классифицировала образец как «{label}» с высокой вероятностью {prob}%. "
            f"Наибольший вклад внесли гены {', '.join(genes)}. "
        )

        if cancer_genes:
            text += (
                f"Среди генов выявлены онкогены ({', '.join(cancer_genes[:3])}), "
                f"что усиливает уверенность в предсказании. "
            )

        if processes:
            text += (
                f"Наблюдается участие в биологических процессах: {', '.join(processes)}. "
            )

        text += (
            "Набор признаков формирует характерный молекулярный паттерн, "
            "используемый для различения данного подтипа опухоли."
        )

        return text

    def _medium_confidence(self, label, prob, genes, cancer_genes, processes):
        text = (
            f"Модель предполагает, что образец относится к «{label}» с вероятностью {prob}%. "
            f"Наибольший вклад в решение внесли гены {', '.join(genes)}. "
        )

        if cancer_genes:
            text += (
                f"Часть из них связана с онкогенными процессами ({', '.join(cancer_genes[:3])}). "
            )

        if processes:
            text += (
                f"Гены участвуют в биологических процессах: {', '.join(processes)}. "
            )

        text += (
            "Наблюдаемая комбинация признаков может соответствовать молекулярному профилю данного подтипа опухоли."
        )

        return text

    def _low_confidence(self, label, prob, genes, cancer_genes, processes):
        text = (
            f"Модель предварительно отнесла образец к классу «{label}» с низкой вероятностью {prob}%. "
            f"Выделенные гены: {', '.join(genes)}. "
        )

        if cancer_genes:
            text += (
                f"Некоторые из них ассоциированы с онкогенными процессами ({', '.join(cancer_genes[:3])}). "
            )

        if processes:
            text += (
                f"Отмечено участие в биологических процессах: {', '.join(processes)}. "
            )

        text += (
            "Однако выраженной согласованности признаков недостаточно для уверенной интерпретации подтипа, "
            "поэтому результат следует рассматривать как предварительный."
        )

        return text

    def _disclaimer(self, text: str) -> str:
        return (
            text
            + "\n\n"
            + "(Данное предсказание носит исследовательский характер и не является медицинским диагнозом. "
              "Результаты не должны использоваться как основание для клинических решений.)"
        )
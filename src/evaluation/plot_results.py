import os
import json
import matplotlib.pyplot as plt
import numpy as np

def generate_plots():
    json_path = os.path.join(os.path.dirname(__file__), 'results_prerecuperacio.json')
    if not os.path.exists(json_path):
        print(f"Error: No s'ha trobat el fitxer {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    metrics = data.get("metrics_summary", {})
    if not metrics:
        print("No hi ha mètriques per visualitzar.")
        return

    # 1. Gràfica de barres per l'Exactitud (Accuracy)
    labels_acc = ['Categoria', 'Urgència', 'Info Faltant']
    values_acc = [
        metrics.get('exactitud_categoria_percent', 0),
        metrics.get('exactitud_urgencia_percent', 0),
        metrics.get('exactitud_informacio_faltant_percent', 0)
    ]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels_acc, values_acc, color=['#4C72B0', '#55A868', '#C44E52'])
    plt.ylim(0, 100)
    plt.title("Exactitud (%) del Mòdul de Prerecuperació", fontsize=14)
    plt.ylabel("Percentatge d'Exactitud (%)", fontsize=12)

    # Afegir els valors damunt de les barres
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{yval}%", ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    acc_path = os.path.join(os.path.dirname(__file__), 'accuracy_plot.png')
    plt.savefig(acc_path, dpi=300)
    plt.close()

    # 2. Gràfica de comparació de la nota mitjana (Nivell de Detall)
    labels_score = ['Mitjana RAG', 'Mitjana Enquesta']
    values_score = [
        metrics.get('nivell_detall_mitja_rag', 0),
        metrics.get('nivell_detall_mitja_enquesta', 0)
    ]

    plt.figure(figsize=(8, 6))
    bars_score = plt.bar(labels_score, values_score, color=['#8172B3', '#64B5CD'], width=0.5)
    plt.ylim(0, 10)
    plt.title("Comparació del Nivell de Detall Mitjà (Escala 0-10)", fontsize=14)
    plt.ylabel("Nota Mitjana", fontsize=12)

    # Afegir MAE i Diferència com a text al gràfic
    mae = metrics.get('nivell_detall_mae', 0)
    diff = metrics.get('nivell_detall_diferencia_mitjanes', 0)
    info_text = f"MAE: {mae}\nDiferència: {diff}"
    plt.text(1.2, 8, info_text, fontsize=12, bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'))

    for bar in bars_score:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2, f"{yval}", ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    score_path = os.path.join(os.path.dirname(__file__), 'score_comparison_plot.png')
    plt.savefig(score_path, dpi=300)
    plt.close()

    # 3. Matriu de Confusió d'Urgència
    import seaborn as sns
    from collections import defaultdict
    import pandas as pd

    y_true_urg = []
    y_pred_urg = []
    for case in data.get("case_by_case_results", []):
        y_true_urg.append(case["ground_truth"]["urgency"])
        y_pred_urg.append(case["rag_prediction"]["urgency"])

    urgency_labels = ['low', 'medium', 'high']
    # Create confusion matrix manually to ensure order
    cm = pd.DataFrame(0, index=urgency_labels, columns=urgency_labels)
    for true_u, pred_u in zip(y_true_urg, y_pred_urg):
        if true_u in urgency_labels and pred_u in urgency_labels:
            cm.loc[true_u, pred_u] += 1

    plt.figure(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
    plt.title('Matriu de Confusió: Urgència', fontsize=14)
    plt.xlabel('Predicció RAG', fontsize=12)
    plt.ylabel('Realitat (Enquesta)', fontsize=12)
    plt.tight_layout()
    urgency_cm_path = os.path.join(os.path.dirname(__file__), 'urgency_confusion_matrix.png')
    plt.savefig(urgency_cm_path, dpi=300)
    plt.close()

    # 4. Desglossament d'Errors de Categoria
    error_counts = defaultdict(int)
    for case in data.get("case_by_case_results", []):
        if not case["metrics"]["category_match"]:
            true_cats = ", ".join(case["ground_truth"]["categories"])
            pred_cat = case["rag_prediction"]["category"]
            error_label = f"Predicció: {pred_cat}\nRealitat: {true_cats}"
            error_counts[error_label] += 1

    if error_counts:
        # Ordenar errors per freqüència
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=False)
        labels_err = [x[0] for x in sorted_errors]
        vals_err = [x[1] for x in sorted_errors]

        plt.figure(figsize=(10, 8))
        plt.barh(labels_err, vals_err, color='#C44E52')
        plt.title('Errors de Classificació de Categoria (Falsos Positius/Negatius)', fontsize=14)
        plt.xlabel('Nombre de Casos Fallats', fontsize=12)
        plt.xticks(range(0, max(vals_err) + 2))
        plt.tight_layout()
        category_err_path = os.path.join(os.path.dirname(__file__), 'category_errors_plot.png')
        plt.savefig(category_err_path, dpi=300)
        plt.close()

    print(f"Gràfiques detallades generades amb èxit a: {os.path.dirname(__file__)}")

if __name__ == '__main__':
    generate_plots()

import numpy as np
import pandas as pd
import os
from joblib import dump
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.stats import uniform, randint
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score, confusion_matrix, roc_curve, auc, classification_report
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

# --- Configuración General ---
RANDOM_STATE = 42
MODEL_DIR = "modelo"
MODEL_FILE = "comovoy.joblib"
DATA_FILE_PATH = "data/dataset.csv"
TARGET_COLUMN = "Aprobado"
TEST_SIZE_RATIO = 0.20
VAL_SIZE_RATIO = 0.25
N_ITER = 60

NUMERIC_FEATURES = [
    'C1', 'C2', 'CR',
    'T_U1_U2', 'T_U3_U5', 'T_Listas', 'T_Texto_Archivos',
    'Ctrl_U1', 'Ctrl_U2', 'Ctrl_U3_Ciclos',
    'Ctrl_U5_Func', 'Ctrl_U6_Strings', 'Ctrl_U7', 'Ctrl_Diccionarios',
    'Ctrl_U10',
    'TS_U1', 'TS_U2', 'TS_U3', 'TS_U5', 'TS_U6', 'TS_U7', 'TS_U8',
    'NEM', 'Puntaje_Ponderado', 'Puntaje_NEM',
    'Puntaje_Ranking', 'Puntaje_Lenguaje', 'Puntaje_Mat_M1',
    'Puntaje_Mat_M2', 'Puntaje_Historia', 'Puntaje_Ciencias',
    'Nota_Test_Ingreso', 'Ano_Egreso'
]

CATEGORICAL_FEATURES = [
    'Género', 'Región', 'Carrera', 'Jornada',
    'Via_Ingreso', 'Rama_Educacional', 'Dependencia'
]

ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def cargar_preprocesar_datos(file_path: str, feature_cols: list, target_col: str):
    try:
        try:
            df = pd.read_csv(file_path, delimiter=';')
        except Exception:
            df = pd.read_csv(file_path, delimiter=',')

        print(f"Datos cargados: {df.shape[0]} registros, {df.shape[1]} columnas.")

        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('.', '', regex=False)

        if target_col not in df.columns:
            raise KeyError(target_col)

        df[target_col] = df[target_col].fillna(0).astype(int)

        missing_feats = [f for f in feature_cols if f not in df.columns]
        if missing_feats:
            print(f"Atención: faltan columnas esperadas: {missing_feats}")
            raise KeyError(f"Faltan features: {missing_feats}")

        X = df[feature_cols].copy()
        y = df[target_col].copy()
        return X, y

    except FileNotFoundError:
        print(f"No se encuentra el archivo: {file_path}")
        raise
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        raise

def entrenar_modelo(X_train: pd.DataFrame, y_train: pd.Series):

    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = OneHotEncoder(
        handle_unknown='ignore',
        sparse_output=False,
        max_categories=10
    )

    preprocesador = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, NUMERIC_FEATURES),
            ('cat', categorical_transformer, CATEGORICAL_FEATURES)
        ]
    )

    full_pipeline = Pipeline(steps=[
        ('preprocesador', preprocesador),
        ('clasificador', GradientBoostingClassifier(random_state=RANDOM_STATE))
    ])

    param_dist = {
        'clasificador__n_estimators': randint(80, 200),
        'clasificador__learning_rate': uniform(0.03, 0.07),
        'clasificador__max_depth': [2, 3],
        'clasificador__min_samples_leaf': [20, 50, 100],
        'clasificador__min_samples_split': [50, 100, 150],
        'clasificador__subsample': uniform(0.5, 0.2),
        'clasificador__max_features': ['sqrt', 'log2'],
    }

    cv_strategy = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    random_search = RandomizedSearchCV(
        estimator=full_pipeline,
        param_distributions=param_dist,
        n_iter=70,
        cv=cv_strategy,
        scoring="roc_auc",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1
    )

    print("\nIniciando RandomizedSearchCV (modelo regularizado)...")
    random_search.fit(X_train, y_train)

    print("\nMejores parámetros encontrados:")
    print(random_search.best_params_)

    return random_search.best_estimator_

def evaluar_modelo(model: Pipeline, X_data: pd.DataFrame, y_true: pd.Series, subset_name: str, umbral: float = 0.5):
    print(f"\n--- Evaluación: {subset_name} (Umbral: {umbral:.2f}---")

    #y_pred = model.predict(X_data)
    y_proba = model.predict_proba(X_data)
    y_proba_riesgo = y_proba[:, 0]
    y_pred = (y_proba_riesgo >= umbral).astype(int)

    target_names = ["Riesgo Alto (0)", "Riesgo Bajo (1)"]
    print(classification_report(y_true, y_pred, target_names=target_names))

    cm = confusion_matrix(y_true, y_pred)
    fpr, tpr, _ = roc_curve(y_true, y_proba_riesgo, pos_label=0)
    roc_auc = auc(fpr, tpr)

    print(f"ROC AUC (clase 0): {roc_auc:.4f}")

    return y_pred, y_proba_riesgo, cm, roc_auc

def plot_metricas(cm, y_test, y_proba_riesgo, roc_auc):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
                xticklabels=['Pred. Riesgo (0)', 'Pred. No Riesgo (1)'],
                yticklabels=['Real Riesgo (0)', 'Real No Riesgo (1)'])
    axes[0].set_title('Matriz de Confusión (Test)')

    fpr, tpr, _ = roc_curve(y_test, y_proba_riesgo, pos_label=0)
    axes[1].plot(fpr, tpr, lw=2, label=f'AUC = {roc_auc:.4f}')
    axes[1].plot([0, 1], [0, 1], linestyle='--', lw=1)
    axes[1].set_title('Curva ROC (Test)')
    axes[1].legend(loc='lower right')

    plt.tight_layout()
    os.makedirs(MODEL_DIR, exist_ok=True)
    plt_path = os.path.join(MODEL_DIR, 'model_evaluation_metrics.png')
    plt.savefig(plt_path)
    plt.show()
    print(f"Gráficos guardados en: {plt_path}")

def main():
    UMBRAL = 0.75
    X, y = cargar_preprocesar_datos(DATA_FILE_PATH, ALL_FEATURES, TARGET_COLUMN)

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=TEST_SIZE_RATIO, random_state=RANDOM_STATE, stratify=y
    )

    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=VAL_SIZE_RATIO, random_state=RANDOM_STATE, stratify=y_train_val
    )

    print("\n--- División de datos ---")
    print(f"Total: {X.shape[0]}  Train: {X_train.shape[0]}  Val: {X_val.shape[0]}  Test: {X_test.shape[0]}")

    best_pipeline = entrenar_modelo(X_train, y_train)

    evaluar_modelo(best_pipeline, X_val, y_val, "Validación")
    y_pred_test, y_proba_riesgo_test, cm_test, roc_auc_test = evaluar_modelo(
        best_pipeline, X_test, y_test, "Prueba",
        UMBRAL
    )

    plot_metricas(cm_test, y_test, y_proba_riesgo_test, roc_auc_test)

    os.makedirs(MODEL_DIR, exist_ok=True)
    dump(best_pipeline, os.path.join(MODEL_DIR, MODEL_FILE))
    print(f"Pipeline guardado en: {os.path.join(MODEL_DIR, MODEL_FILE)}")


if __name__ == '__main__':
    main()

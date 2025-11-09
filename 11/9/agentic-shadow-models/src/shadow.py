from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics.pairwise import cosine_similarity

class ShadowModel:
    """Text-to-text approximator using classification over known templates.
    Confidence is estimated via cosine similarity in TF-IDF space and model probability.
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1)
        self.clf = SGDClassifier(loss="log_loss", max_iter=1000, tol=1e-3, random_state=7)
        self.pipeline = Pipeline([("tfidf", self.vectorizer), ("clf", self.clf)])
        self.templates_ = []
        self.fitted_ = False

    def fit(self, X: List[str], y: List[str]):
        self.templates_ = sorted(set(y))
        y_ids = [self.templates_.index(t) for t in y]
        self.pipeline.fit(X, y_ids)
        self.fitted_ = True
        return self

    def partial_fit(self, X: List[str], y: List[str]):
        if not self.fitted_:
            return self.fit(X, y)
        y_ids = [self.templates_.index(t) if t in self.templates_ else self._add_template(t) for t in y]
        self.pipeline.named_steps["clf"].partial_fit(
            self.pipeline.named_steps["tfidf"].transform(X), y_ids, classes=list(range(len(self.templates_)))
        )
        return self

    def _add_template(self, t: str):
        self.templates_.append(t)
        return len(self.templates_) - 1

    def predict(self, x: str) -> Tuple[str, float]:
        if not self.fitted_:
            return "", 0.0
        X_vec = self.pipeline.named_steps["tfidf"].transform([x])
        proba = getattr(self.pipeline.named_steps["clf"], "predict_proba", None)
        if proba is not None:
            probs = self.pipeline.named_steps["clf"].predict_proba(X_vec)[0]
            idx = int(np.argmax(probs))
            conf_model = float(np.max(probs))
        else:
            idx = int(self.pipeline.named_steps["clf"].predict(X_vec)[0])
            conf_model = 0.5
        # cosine similarity to nearest training template vector as additional confidence
        tmpl_vecs = self.pipeline.named_steps["tfidf"].transform(self.templates_)
        sims = cosine_similarity(X_vec, tmpl_vecs)[0]
        conf_sem = float(np.max(sims))
        conf = float(0.6 * conf_model + 0.4 * conf_sem)
        return self.templates_[idx], conf

"""
Pre-train the DNN and PINN models and cache them to static/models/models.pkl.

Run this once (after changing data or hyperparameters) so production
deployments (e.g. Vercel) load the models instantly instead of spending
30-60 s retraining on every cold start.

    python train_models.py
"""

import app

if __name__ == "__main__":
    print("Training models (this takes ~30-60 s)...")
    app.get_models()
    print("Saved -> " + app.MODEL_CACHE)

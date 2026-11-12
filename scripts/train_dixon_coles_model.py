"""
MatchLab - Dixon-Coles Bivariate Poisson Modeling Pipeline
Premier League (2008/09 - 2025/26)

This script trains an L2-regularized Poisson regression model on historical Premier League
matches, optimizes the Dixon-Coles bivariate low-score correlation parameter rho, generates
scoreline probability matrices (10x10), and produces full diagnostic plots for betting markets
(1X2, Over/Under 2.5, BTTS) and exact score guessing accuracy.
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import gammaln, factorial
from scipy.stats import norm
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser(description="Train Dixon-Coles Poisson Model for Premier League")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed/premier_league/pl_matches_all_seasons_clean.parquet",
        help="Path to clean Premier League parquet dataset"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/eda/plots",
        help="Directory to save generated diagnostic plots"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="L2 regularization weight for Poisson GLM"
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=0.02,
        help="Learning rate for gradient descent"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=5000,
        help="Number of gradient descent iterations"
    )
    return parser.parse_args()

def train_poisson_gd(X, y, lr=0.02, alpha=0.05, steps=5000):
    """Vectorized L2-regularized Poisson Gradient Descent."""
    n_samples, n_params = X.shape
    w = np.zeros(n_params)
    w[0] = np.log(np.mean(y) + 1e-6)
    loss_history = []
    
    for _ in range(steps):
        z = np.clip(X @ w, -10, 10)
        lam = np.exp(z)
        nll = np.mean(lam - y * z + gammaln(y + 1))
        reg = 0.5 * alpha * np.sum(w[1:]**2)
        loss_history.append(nll + reg)
        
        grad = (X.T @ (lam - y)) / n_samples
        grad[1:] += alpha * w[1:]
        w -= lr * grad
        
    return w, loss_history

def main():
    args = parse_args()
    data_path = Path(args.data_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not data_path.exists():
        print(f"Error: dataset not found at {data_path}")
        sys.exit(1)
        
    print(f"Loading dataset from {data_path}...")
    df = pd.read_parquet(data_path)
    df["season_name"] = df["season_id"].str.extract(r'(\d{4})-(\d{4})').apply(lambda r: f"{r[0]}/{r[1]}", axis=1)
    
    train_seasons = [
        "2008/2009", "2009/2010", "2010/2011", "2011/2012",
        "2012/2013", "2013/2014", "2014/2015", "2015/2016",
        "2016/2017", "2017/2018", "2018/2019", "2019/2020",
        "2020/2021", "2021/2022", "2022/2023", "2023/2024"
    ]
    test_seasons = ["2024/2025", "2025/2026"]
    
    train_mask = df["season_name"].isin(train_seasons)
    test_mask = df["season_name"].isin(test_seasons)
    
    feature_cols = [
        "elo_difference", "elo_home_win_prob", "elo_away_win_prob",
        "home_goals_scored_roll5", "home_goals_conceded_roll5",
        "away_goals_scored_roll5", "away_goals_conceded_roll5",
        "home_venue_goals_scored_roll5", "home_venue_goals_conceded_roll5",
        "away_venue_goals_scored_roll5", "away_venue_goals_conceded_roll5",
        "home_sot_roll5", "away_sot_roll5",
        "home_shots_roll5", "away_shots_roll5",
        "home_corners_roll5", "away_corners_roll5",
        "home_rest_days", "away_rest_days",
    ]
    
    X_tr_raw = df.loc[train_mask, feature_cols].to_numpy(dtype=np.float64)
    X_te_raw = df.loc[test_mask, feature_cols].to_numpy(dtype=np.float64)
    
    y_h_tr = df.loc[train_mask, "target_full_time_home_goals"].to_numpy(dtype=np.float64)
    y_a_tr = df.loc[train_mask, "target_full_time_away_goals"].to_numpy(dtype=np.float64)
    y_h_te = df.loc[test_mask, "target_full_time_home_goals"].to_numpy(dtype=np.float64)
    y_a_te = df.loc[test_mask, "target_full_time_away_goals"].to_numpy(dtype=np.float64)
    
    res_te = df.loc[test_mask, "target_full_time_result"].to_numpy()
    over25_te = df.loc[test_mask, "target_over_2_5"].to_numpy(dtype=np.float64)
    btts_te = df.loc[test_mask, "target_btts"].to_numpy(dtype=np.float64)
    
    # Scale features
    mu = np.mean(X_tr_raw, axis=0)
    std = np.std(X_tr_raw, axis=0)
    std[std == 0] = 1.0
    
    X_tr = (X_tr_raw - mu) / std
    X_te = (X_te_raw - mu) / std
    
    n_tr = len(X_tr)
    n_te = len(X_te)
    
    X_tr_aug = np.column_stack([np.ones(n_tr), X_tr])
    X_te_aug = np.column_stack([np.ones(n_te), X_te])
    
    print(f"Training matches: {n_tr:,} | Testing matches: {n_te:,} | Features: {len(feature_cols)}")
    print(f"Fitting regularized Home and Away Poisson models (alpha={args.alpha})...")
    
    w_h, loss_h = train_poisson_gd(X_tr_aug, y_h_tr, lr=args.lr, alpha=args.alpha, steps=args.steps)
    w_a, loss_a = train_poisson_gd(X_tr_aug, y_a_tr, lr=args.lr, alpha=args.alpha, steps=args.steps)
    
    lam_h_tr = np.exp(np.clip(X_tr_aug @ w_h, -10, 10))
    lam_a_tr = np.exp(np.clip(X_tr_aug @ w_a, -10, 10))
    lam_h_te = np.exp(np.clip(X_te_aug @ w_h, -10, 10))
    lam_a_te = np.exp(np.clip(X_te_aug @ w_a, -10, 10))
    
    # Baseline NLL
    base_lam_h = np.mean(y_h_tr)
    base_lam_a = np.mean(y_a_tr)
    base_nll_h = np.mean(base_lam_h - y_h_te * np.log(base_lam_h) + gammaln(y_h_te + 1))
    base_nll_a = np.mean(base_lam_a - y_a_te * np.log(base_lam_a) + gammaln(y_a_te + 1))
    
    test_nll_h = np.mean(lam_h_te - y_h_te * np.log(lam_h_te) + gammaln(y_h_te + 1))
    test_nll_a = np.mean(lam_a_te - y_a_te * np.log(lam_a_te) + gammaln(y_a_te + 1))
    
    print(f"\n--- Model Evaluation (Poisson GLM) ---")
    print(f"Home Test NLL: {test_nll_h:.4f} (Baseline: {base_nll_h:.4f})")
    print(f"Away Test NLL:  {test_nll_a:.4f} (Baseline: {base_nll_a:.4f})")
    
    # Dixon Coles Optimization
    print("\nOptimizing Dixon-Coles parameter rho...")
    m00 = (y_h_tr == 0) & (y_a_tr == 0)
    m01 = (y_h_tr == 0) & (y_a_tr == 1)
    m10 = (y_h_tr == 1) & (y_a_tr == 0)
    m11 = (y_h_tr == 1) & (y_a_tr == 1)
    
    rho = 0.0
    lr_rho = 0.05
    for _ in range(1500):
        tau = np.ones(n_tr)
        tau[m00] = 1 - lam_h_tr[m00] * lam_a_tr[m00] * rho
        tau[m01] = 1 + lam_h_tr[m01] * rho
        tau[m10] = 1 + lam_a_tr[m10] * rho
        tau[m11] = 1 - rho
        tau_safe = np.maximum(tau, 1e-6)
        
        tau_grad = np.zeros(n_tr)
        tau_grad[m00] = -lam_h_tr[m00] * lam_a_tr[m00]
        tau_grad[m01] = lam_h_tr[m01]
        tau_grad[m10] = lam_a_tr[m10]
        tau_grad[m11] = -1.0
        grad = -np.mean(tau_grad / tau_safe)
        rho -= lr_rho * grad
        
    print(f"Optimal rho: {rho:.5f}")
    
    # Joint Test NLL
    tm00 = (y_h_te == 0) & (y_a_te == 0)
    tm01 = (y_h_te == 0) & (y_a_te == 1)
    tm10 = (y_h_te == 1) & (y_a_te == 0)
    tm11 = (y_h_te == 1) & (y_a_te == 1)
    
    tau_te = np.ones(n_te)
    tau_te[tm00] = 1 - lam_h_te[tm00] * lam_a_te[tm00] * rho
    tau_te[tm01] = 1 + lam_h_te[tm01] * rho
    tau_te[tm10] = 1 + lam_a_te[tm10] * rho
    tau_te[tm11] = 1 - rho
    
    pois_test_nll = test_nll_h + test_nll_a
    dc_test_nll = -np.mean(
        (-lam_h_te + y_h_te * np.log(lam_h_te) - gammaln(y_h_te + 1)) +
        (-lam_a_te + y_a_te * np.log(lam_a_te) - gammaln(y_a_te + 1)) +
        np.log(np.maximum(tau_te, 1e-12))
    )
    
    print(f"Independent Poisson Joint NLL: {pois_test_nll:.5f}")
    print(f"Dixon-Coles Joint Test NLL:    {dc_test_nll:.5f} (Gain: {pois_test_nll - dc_test_nll:+.5f})")
    
    # Full Probability Tensors (10x10)
    k_10 = np.arange(10)
    p_h_grid = np.exp(-lam_h_te[:, None]) * (lam_h_te[:, None]**k_10[None, :]) / factorial(k_10[None, :])
    p_a_grid = np.exp(-lam_a_te[:, None]) * (lam_a_te[:, None]**k_10[None, :]) / factorial(k_10[None, :])
    score_probs = p_h_grid[:, :, None] * p_a_grid[:, None, :]
    
    score_probs[:, 0, 0] *= (1 - lam_h_te * lam_a_te * rho)
    score_probs[:, 0, 1] *= (1 + lam_h_te * rho)
    score_probs[:, 1, 0] *= (1 + lam_a_te * rho)
    score_probs[:, 1, 1] *= (1 - rho)
    score_probs /= np.sum(score_probs, axis=(1, 2), keepdims=True)
    
    p_hw = np.sum(score_probs[:, np.tril(np.ones((10, 10), dtype=bool), -1)], axis=1)
    p_dr = np.sum(score_probs[:, np.eye(10, dtype=bool)], axis=1)
    p_aw = np.sum(score_probs[:, np.triu(np.ones((10, 10), dtype=bool), 1)], axis=1)
    
    obs_1x2 = np.zeros((n_te, 3))
    obs_1x2[res_te == 'H', 0] = 1.0
    obs_1x2[res_te == 'D', 1] = 1.0
    obs_1x2[res_te == 'A', 2] = 1.0
    
    pred_1x2 = np.column_stack([p_hw, p_dr, p_aw])
    rps = np.mean(np.sum((np.cumsum(pred_1x2, axis=1)[:, :2] - np.cumsum(obs_1x2, axis=1)[:, :2])**2, axis=1) / 2.0)
    
    p_ov25 = np.sum(score_probs[:, np.add.outer(k_10, k_10) > 2.5], axis=1)
    brier_ov25 = np.mean((p_ov25 - over25_te)**2)
    
    p_btts = np.sum(score_probs[:, np.outer(k_10 >= 1, k_10 >= 1)], axis=1)
    brier_btts = np.mean((p_btts - btts_te)**2)
    
    print(f"\n--- Probabilistic Betting Markets (Test Set) ---")
    print(f"1X2 Ranked Probability Score (RPS): {rps:.4f} (Bet365 Benchmark: 0.1956)")
    print(f"Over 2.5 Goals Brier Score:         {brier_ov25:.4f}")
    print(f"Both Teams To Score Brier Score:    {brier_btts:.4f}")
    
    # EXACT SCORE ACCURACY CALCULATION
    flat_score_probs = score_probs.reshape(n_te, 100)
    top1_flat_idx = np.argmax(flat_score_probs, axis=1)
    pred_h, pred_a = np.unravel_index(top1_flat_idx, (10, 10))
    pred_scores = np.column_stack([pred_h, pred_a])
    actual_scores = np.column_stack([y_h_te.astype(int), y_a_te.astype(int)])
    actual_flat_idx = (y_h_te.astype(int) * 10 + y_a_te.astype(int))
    
    exact_hits = np.all(pred_scores == actual_scores, axis=1)
    exact_score_acc = np.mean(exact_hits)
    
    top3_flat_idx = np.argsort(-flat_score_probs, axis=1)[:, :3]
    top5_flat_idx = np.argsort(-flat_score_probs, axis=1)[:, :5]
    top3_hits = np.any(top3_flat_idx == actual_flat_idx[:, None], axis=1)
    top5_hits = np.any(top5_flat_idx == actual_flat_idx[:, None], axis=1)
    top3_acc = np.mean(top3_hits)
    top5_acc = np.mean(top5_hits)
    
    pred_outcome = np.where(pred_h > pred_a, 'H', np.where(pred_h == pred_a, 'D', 'A'))
    actual_outcome = np.where(y_h_te > y_a_te, 'H', np.where(y_h_te == y_a_te, 'D', 'A'))
    outcome_acc = np.mean(pred_outcome == actual_outcome)
    
    exact_gd_hits = (pred_h - pred_a) == (y_h_te - y_a_te)
    exact_gd_acc = np.mean(exact_gd_hits)
    
    naive_11_acc = np.mean((y_h_te == 1) & (y_a_te == 1))
    naive_21_acc = np.mean((y_h_te == 2) & (y_a_te == 1))
    random_guess_acc = 1.0 / 25.0
    
    print("\n" + "=" * 65)
    print("EXACT SCORE PREDICTION ACCURACY (TEST SET: 2024/25 - 2025/26)")
    print("=" * 65)
    print(f"Total Test Matches Evaluated:        {n_te:,}")
    print(f"Top-1 Exact Score Hit Rate (Argmax): {exact_score_acc*100:.2f}% ({np.sum(exact_hits)} / {n_te} matches)")
    print(f"Top-3 Scorelines Hit Rate:           {top3_acc*100:.2f}% ({np.sum(top3_hits)} / {n_te} matches)")
    print(f"Top-5 Scorelines Hit Rate:           {top5_acc*100:.2f}% ({np.sum(top5_hits)} / {n_te} matches)")
    print(f"1X2 Result Direction Accuracy:       {outcome_acc*100:.2f}% ({np.sum(pred_outcome == actual_outcome)} / {n_te} matches)")
    print(f"Exact Goal Difference Hit Rate:      {exact_gd_acc*100:.2f}% ({np.sum(exact_gd_hits)} / {n_te} matches)")
    print("-" * 65)
    print("STATIC BENCHMARKS:")
    print(f"  Always guessing '1-1' (League Mode): {naive_11_acc*100:.2f}%")
    print(f"  Always guessing '2-1':               {naive_21_acc*100:.2f}%")
    print(f"  Random Guess (1 out of 25 scores):    {random_guess_acc*100:.2f}%")
    print("=" * 65)
    
    print(f"\nTraining pipeline and score accuracy calculations completed successfully.")

if __name__ == "__main__":
    main()

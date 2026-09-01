#!/usr/bin/env python3
"""
Prototype: CLIP-embedding icon-similarity cache (strategy 2 from u_3219 — visual
recognition by prior experience, as opposed to trial-and-observe in explore_and_cache.py).

Encodes an icon crop into a CLIP image embedding, stores it keyed by a human-given
label, and matches future crops via cosine similarity. No gradient training — this
is zero-shot reuse of a pretrained model, per u_3216's question about single-example
learning feasibility.

Requires (one-time install, not yet done — verify before installing per network-budget rule):
  pip install open_clip_torch pillow

Usage:
  python3 clip_embed_cache.py learn --image <path> --label <name>
  python3 clip_embed_cache.py match --image <path>
  python3 clip_embed_cache.py list
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

CACHE_PATH = Path(__file__).parent / "clip_icon_cache.json"
MODEL_NAME = "ViT-B-32"
PRETRAINED = "openai"

_model = None
_preprocess = None


def _load_model():
    global _model, _preprocess
    if _model is not None:
        return _model, _preprocess
    import open_clip
    import torch

    model, _, preprocess = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=PRETRAINED)
    model.eval()
    _model, _preprocess = model, preprocess
    return _model, _preprocess


def embed_image(image_path):
    import torch

    model, preprocess = _load_model()
    image = Image.open(image_path).convert("RGB")
    tensor = preprocess(image).unsqueeze(0)
    with torch.no_grad():
        features = model.encode_image(tensor)
        features = features / features.norm(dim=-1, keepdim=True)
    return features.squeeze(0).numpy()


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def learn(image_path, label):
    cache = load_cache()
    embedding = embed_image(image_path)
    cache[label] = {"embedding": embedding.tolist(), "source_image": str(image_path)}
    save_cache(cache)
    print(f"learned '{label}' from {image_path} (embedding dim={len(embedding)})")


def match(image_path, threshold=0.90):
    cache = load_cache()
    if not cache:
        print("cache empty, nothing to match against")
        return None
    query_embedding = embed_image(image_path)
    scores = []
    for label, entry in cache.items():
        sim = cosine_similarity(query_embedding, entry["embedding"])
        scores.append((label, sim))
    scores.sort(key=lambda x: -x[1])
    print("similarity ranking:")
    for label, sim in scores:
        marker = " <-- MATCH" if sim >= threshold else ""
        print(f"  {label}: {sim:.4f}{marker}")
    best_label, best_sim = scores[0]
    if best_sim >= threshold:
        return best_label, best_sim
    return None, best_sim


def list_cache():
    cache = load_cache()
    if not cache:
        print("cache empty")
        return
    for label, entry in cache.items():
        print(f"{label}: source={entry['source_image']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_learn = sub.add_parser("learn")
    p_learn.add_argument("--image", required=True)
    p_learn.add_argument("--label", required=True)

    p_match = sub.add_parser("match")
    p_match.add_argument("--image", required=True)
    p_match.add_argument("--threshold", type=float, default=0.90)

    sub.add_parser("list")

    args = parser.parse_args()
    if args.cmd == "learn":
        learn(args.image, args.label)
    elif args.cmd == "match":
        match(args.image, args.threshold)
    elif args.cmd == "list":
        list_cache()

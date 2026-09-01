#!/usr/bin/env python3
"""
Prototype: small CNN icon-function classifier, trained on boostvolt/icon-dataset
(internal-research-only per DATA_SOURCES.md policy).

Follows Rico's 94%-accuracy icon classifier as the reference target — small purpose-trained
model beats generic CLIP zero-shot(ar_2983 showed CLIP fails, 0% discriminative gap).

Usage:
  python3 train_icon_cnn.py train --data-dir <path-to-icon-dataset> --epochs 10
  python3 train_icon_cnn.py eval --model checkpoint.pt --data-dir <path> --split test
  python3 train_icon_cnn.py predict --model checkpoint.pt --image <path>
"""
import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

CHECKPOINT_PATH = Path(__file__).parent / "icon_cnn_checkpoint.pt"
LABELS_PATH = Path(__file__).parent / "icon_cnn_labels.json"

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# data augmentation for TRAIN split only(u_3258 option3) — icons are simple flat-color shapes,
# so augmentation stays mild(small rotation/color-jitter/crop) to avoid distorting recognizability
TRAIN_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomRotation(degrees=10),
    transforms.ColorJitter(brightness=0.15, contrast=0.15),
    transforms.RandomResizedCrop(224, scale=(0.85, 1.0)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def build_model(num_classes):
    # ResNet18 backbone, small+fast, standard transfer-learning baseline
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def train(data_dir, epochs, batch_size=32, lr=1e-3):
    t0 = time.time()
    train_dir = Path(data_dir) / "train"
    val_dir = Path(data_dir) / "val"
    if not train_dir.exists():
        raise FileNotFoundError(f"expected {train_dir} — check dataset layout matches ImageFolder convention")

    train_ds = datasets.ImageFolder(train_dir, transform=TRAIN_TRANSFORM)
    val_ds = datasets.ImageFolder(val_dir, transform=TRANSFORM)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    num_classes = len(train_ds.classes)
    model = build_model(num_classes).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    # cosine LR decay(u_3258 option2) — smooth reduction over the full run, good for fine-tuning tail
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # class weights(u_3265/3266) — ar_2988 found attach class has only 12 samples vs 150-500+
    # for other classes, causing 0% accuracy regardless of epochs/augmentation. Inverse-frequency
    # weighting makes underrepresented classes penalize misclassification more heavily.
    class_counts = [0] * num_classes
    for _, label in train_ds.samples:
        class_counts[label] += 1
    total_samples = sum(class_counts)
    class_weights = torch.tensor(
        [total_samples / (num_classes * count) for count in class_counts],
        dtype=torch.float32,
    ).to(DEVICE)
    print(f"class weight range: min={class_weights.min().item():.2f} max={class_weights.max().item():.2f}")
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    LABELS_PATH.write_text(json.dumps(train_ds.classes, indent=2))

    for epoch in range(epochs):
        epoch_t0 = time.time()
        model.train()
        total_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == labels).sum().item()
                total += labels.size(0)
        val_acc = correct / total if total > 0 else 0.0
        epoch_time = time.time() - epoch_t0
        current_lr = scheduler.get_last_lr()[0]
        print(f"epoch {epoch+1}/{epochs}: loss={total_loss/len(train_loader):.4f} val_acc={val_acc:.4f} lr={current_lr:.6f} time={epoch_time:.1f}s")
        scheduler.step()

        # per-epoch checkpoint: survives a hang/kill on the FINAL save without losing progress
        tmp_path = CHECKPOINT_PATH.with_suffix(".pt.tmp")
        torch.save(model.state_dict(), tmp_path)
        tmp_path.replace(CHECKPOINT_PATH)
        print(f"  checkpoint saved after epoch {epoch+1}")

    # final save omitted — per-epoch checkpoint above already holds the last epoch's
    # weights; a redundant final torch.save() reliably hung on MPS(ar_2986), no benefit
    total_time = time.time() - t0
    checkpoint_size_mb = CHECKPOINT_PATH.stat().st_size / (1024 * 1024)
    print(f"\ntraining complete: total_time={total_time:.1f}s checkpoint_size={checkpoint_size_mb:.1f}MB device={DEVICE}")
    print(f"classes={num_classes} train_samples={len(train_ds)} val_samples={len(val_ds)}")


def evaluate(model_path, data_dir, split="test"):
    labels = json.loads(LABELS_PATH.read_text())
    model = build_model(len(labels))
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    test_dir = Path(data_dir) / split
    test_ds = datasets.ImageFolder(test_dir, transform=TRANSFORM)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)

    correct, total = 0, 0
    per_class_correct = {}
    per_class_total = {}
    t0 = time.time()
    with torch.no_grad():
        for images, targets in test_loader:
            images, targets = images.to(DEVICE), targets.to(DEVICE)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == targets).sum().item()
            total += targets.size(0)
            for t, p in zip(targets.cpu().numpy(), predicted.cpu().numpy()):
                cls = test_ds.classes[t]
                per_class_total[cls] = per_class_total.get(cls, 0) + 1
                if t == p:
                    per_class_correct[cls] = per_class_correct.get(cls, 0) + 1

    inference_time = time.time() - t0
    accuracy = correct / total if total > 0 else 0.0
    print(f"\n{split} accuracy: {correct}/{total} = {accuracy:.4f}")
    print(f"inference time for {total} images: {inference_time:.2f}s ({inference_time/total*1000:.1f}ms/image)")
    print("\nworst 10 classes by accuracy:")
    class_accs = [(c, per_class_correct.get(c, 0) / per_class_total[c]) for c in per_class_total]
    class_accs.sort(key=lambda x: x[1])
    for cls, acc in class_accs[:10]:
        print(f"  {cls}: {acc:.2f} ({per_class_correct.get(cls,0)}/{per_class_total[cls]})")


def predict(model_path, image_path):
    from PIL import Image

    labels = json.loads(LABELS_PATH.read_text())
    model = build_model(len(labels))
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    image = Image.open(image_path).convert("RGB")
    tensor = TRANSFORM(image).unsqueeze(0).to(DEVICE)
    t0 = time.time()
    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)
        top5 = torch.topk(probs, 5)
    infer_time = (time.time() - t0) * 1000
    print(f"inference time: {infer_time:.1f}ms")
    for prob, idx in zip(top5.values[0], top5.indices[0]):
        print(f"  {labels[idx]}: {prob.item():.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_train = sub.add_parser("train")
    p_train.add_argument("--data-dir", required=True)
    p_train.add_argument("--epochs", type=int, default=10)
    p_train.add_argument("--batch-size", type=int, default=32)

    p_eval = sub.add_parser("eval")
    p_eval.add_argument("--model", default=str(CHECKPOINT_PATH))
    p_eval.add_argument("--data-dir", required=True)
    p_eval.add_argument("--split", default="test")

    p_predict = sub.add_parser("predict")
    p_predict.add_argument("--model", default=str(CHECKPOINT_PATH))
    p_predict.add_argument("--image", required=True)

    args = parser.parse_args()
    if args.cmd == "train":
        train(args.data_dir, args.epochs, args.batch_size)
    elif args.cmd == "eval":
        evaluate(args.model, args.data_dir, args.split)
    elif args.cmd == "predict":
        predict(args.model, args.image)

"""a_5612 D2 차로ID 분할망(2026-09-24): 작은 U-Net. 입력 3×256×256(preprocess 동일), 출력 12클래스 로짓 256×256
(0 도로밖 1..8 내 방향 k차로 9 차선 10 반대 11 교차로). 인코더 = DriveNet 형(stride-2 ×5), 디코더 = 스킵 + 최근접 업샘플. 픽셀만 입력."""
import torch, torch.nn as nn, torch.nn.functional as F
NCLS = 12
def cbr(i, o, k=3, s=1): return nn.Sequential(nn.Conv2d(i, o, k, s, k // 2), nn.BatchNorm2d(o), nn.ReLU(inplace=True))
class SegNet(nn.Module):
    def __init__(self, ncls=NCLS, w=(16, 32, 64, 96, 128)):
        super().__init__(); self.ncls = ncls
        self.e = nn.ModuleList([nn.Sequential(cbr(3 if i == 0 else w[i - 1], c, 3, 2), cbr(c, c)) for i, c in enumerate(w)])   # 256→128→64→32→16→8
        self.d = nn.ModuleList([nn.Sequential(cbr(w[i] + w[i - 1], w[i - 1]), cbr(w[i - 1], w[i - 1])) for i in range(len(w) - 1, 0, -1)])   # 8→16→…→128
        self.head = nn.Sequential(cbr(w[0], w[0]), nn.Conv2d(w[0], ncls, 1))   # 128 로짓 → ×2 업샘플(입력 해상도)
    def forward(self, x):
        fs = []
        for e in self.e: x = e(x); fs.append(x)
        x = fs[-1]
        for i, d in enumerate(self.d):
            skip = fs[-2 - i]; x = F.interpolate(x, size=skip.shape[-2:], mode='nearest'); x = d(torch.cat([x, skip], 1))
        return F.interpolate(self.head(x), scale_factor=2, mode='bilinear', align_corners=False)
if __name__ == '__main__':
    n = SegNet(); print(sum(p.numel() for p in n.parameters()) / 1e6, 'M', n(torch.zeros(1, 3, 256, 256)).shape)

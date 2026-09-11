import os
import glob
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

class cfg:
    bs = 32
    num_workers = 3
    inp_dim = (3, 32, 32)
    train_steps = 20000

class CIFARDataset(Dataset):
    def __init__(self, path):
        self.files = glob.glob(path)
        self.labels_map = {
            "airplane": 0, "automobile": 1, "bird": 2, "cat": 3,
            "deer": 4, "dog": 5, "frog": 6, "horse": 7,
            "ship": 8, "truck": 9
        }
        # Assuming images are standard 8-bit pngs. ToTensor converts to [0,1] float32.
        self.transform = transforms.ToTensor()

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        file_path = self.files[idx]
        img = Image.open(file_path).convert('RGB')
        x = self.transform(img)
        
        # Replicating logic: aux.split('.')[0].split('_')[-1]
        filename = os.path.basename(file_path)
        aux = filename.split('.')[0].split('_')[-1]
        y = self.labels_map[aux]
        
        return x, y

class ResidualModule(nn.Module):
    def __init__(self, m, n, stride):
        super().__init__()
        self.has_skip = (m != n) or (stride > 1)
        
        self.c1 = nn.Conv2d(m, n, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(n, eps=1e-5, momentum=0.1)
        
        self.c2 = nn.Conv2d(n, n, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(n, eps=1e-5, momentum=0.1)
        
        if self.has_skip:
            self.c_skip = nn.Conv2d(m, n, kernel_size=1, stride=stride, padding=0, bias=False)
            self.bn_skip = nn.BatchNorm2d(n, eps=1e-5, momentum=0.1)
            
    def forward(self, x):
        z = x
        x = self.c1(x)
        x = self.bn1(x)
        x = F.relu(x)
        
        x = self.c2(x)
        x = self.bn2(x)
        x = F.relu(x)  # Replicating pseudo-code exact order
        
        if self.has_skip:
            z = self.c_skip(z)
            z = self.bn_skip(z)
            
        x = x + z
        return x

class ResidualBlock(nn.Module):
    def __init__(self, m, n, stride):
        super().__init__()
        self.b1 = ResidualModule(m, n, stride)
        self.b2 = ResidualModule(n, n, 1)
        self.b3 = ResidualModule(n, n, 1)
        
    def forward(self, x):
        x = self.b1(x)
        x = self.b2(x)
        x = self.b3(x)
        return x

class ResNet18(nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = nn.Conv2d(3, 16, kernel_size=3, stride=1, padding=1, bias=False)
        self.b1 = ResidualBlock(16, 16, 1)
        self.b2 = ResidualBlock(16, 32, 2)
        self.b3 = ResidualBlock(32, 64, 2)
        
        self.pool = nn.AvgPool2d(kernel_size=8, stride=1, padding=0)
        
        self.l1 = nn.Linear(64, 10)
        # "xavu" -> Xavier Uniform initialization
        nn.init.xavier_uniform_(self.l1.weight)
        nn.init.zeros_(self.l1.bias)
        
    def forward(self, x):
        x = self.c1(x)
        x = self.b1(x)
        x = self.b2(x)
        x = self.b3(x)
        
        x = self.pool(x)
        
        x = x.view(x.size(0), -1)
        x = F.relu(x)
        x = self.l1(x)
        return x

def train(model, device):
    model.train()
    dataset = CIFARDataset("/frost_exp/Neve_benchmarks/cifar/train/*.png")
    dataloader = DataLoader(dataset, batch_size=cfg.bs, shuffle=True, 
                            num_workers=cfg.num_workers, drop_last=True)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.0001, betas=(0.9, 0.98))
    criterion = nn.CrossEntropyLoss()
    
    data_iter = iter(dataloader)
    
    for i in range(cfg.train_steps):
        try:
            a, b = next(data_iter)
        except StopIteration:
            # Re-initialize dataloader iterator when epoch ends
            data_iter = iter(dataloader)
            a, b = next(data_iter)
            
        a, b = a.to(device), b.to(device)
        
        optimizer.zero_grad()
        y_hat = model(a)
        loss = criterion(y_hat, b)
        loss.backward()
        optimizer.step()
        
        if i % 100 == 0:
            print(f"i: {i} -- Loss: {loss.item():.4f}")

def evaluate(model, device):
    model.eval()
    dataset = CIFARDataset("/frost_exp/Neve_benchmarks/cifar/test/*.png")
    dataloader = DataLoader(dataset, batch_size=cfg.bs, shuffle=False, 
                            num_workers=cfg.num_workers, drop_last=True)
    
    acc = 0.0
    steps = len(dataloader)
    
    with torch.no_grad():
        for i, (a, b) in enumerate(dataloader):
            a, b = a.to(device), b.to(device)
            y_hat = model(a)
            
            preds = y_hat.argmax(dim=1)
            eq_mask = (preds == b).float()
            local_acc = eq_mask.mean()
            acc += local_acc.item()
            
            if i % 100 == 0:
                print(f"val {i}")
                
    acc /= steps
    print("Accuracy")
    print(f"{acc:.4f}")

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ResNet18().to(device)
    
    train(model, device)
    evaluate(model, device)

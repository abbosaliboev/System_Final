"""
TCN with Attention Model for Fall Detection
10 keypoint version - optimized for real-time inference
"""
import torch
import torch.nn as nn


class TCN_Attention_Model(nn.Module):
    """
    Temporal Convolutional Network with Multi-Head Attention.
    
    Architecture:
    - Input: [batch, sequence_length=30, input_size=20] (10 keypoints × 2)
    - TCN: Conv1D layers with BatchNorm and Dropout
    - Attention: Multi-head attention mechanism
    - Output: [batch, num_classes=2] (no_fall, fall)
    """
    
    def __init__(self, input_size=20, num_classes=2, num_channels=[64, 128, 256], 
                 kernel_size=3, dropout=0.2):
        super(TCN_Attention_Model, self).__init__()
        
        # TCN layers
        layers = []
        in_ch = input_size
        for out_ch in num_channels:
            layers += [
                nn.Conv1d(in_ch, out_ch, kernel_size, padding=(kernel_size-1)//2),
                nn.BatchNorm1d(out_ch),
                nn.ReLU(),
                nn.Dropout(dropout)
            ]
            in_ch = out_ch
        self.tcn = nn.Sequential(*layers)
        
        # Multi-head attention (lightweight replacement for Transformer)
        self.attention = nn.MultiheadAttention(
            embed_dim=num_channels[-1], 
            num_heads=4, 
            batch_first=True
        )
        
        # Classification head
        self.fc = nn.Linear(num_channels[-1], num_classes)

    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: [batch, sequence_length, input_size] - normalized keypoints
        
        Returns:
            logits: [batch, num_classes] - classification scores
        """
        # x: [batch, 30, 20] -> [batch, 20, 30]
        x = x.transpose(1, 2)
        
        # TCN processing
        x = self.tcn(x)
        
        # x: [batch, 256, 30] -> [batch, 30, 256]
        x = x.transpose(1, 2)
        
        # Self-attention
        attn_out, _ = self.attention(x, x, x)
        
        # Take last frame features
        out = attn_out[:, -1, :]
        
        # Classification
        return self.fc(out)

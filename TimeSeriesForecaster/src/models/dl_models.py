"""Deep Learning models for time series forecasting."""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Optional, Union, Tuple
import logging
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """PyTorch Dataset for time series data."""

    def __init__(
        self,
        data: np.ndarray,
        sequence_length: int,
        horizon: int = 1
    ):
        """
        Initialize dataset.

        Args:
            data: Time series data
            sequence_length: Length of input sequences
            horizon: Forecast horizon
        """
        self.data = data
        self.sequence_length = sequence_length
        self.horizon = horizon

    def __len__(self) -> int:
        return len(self.data) - self.sequence_length - self.horizon + 1

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.data[idx:idx + self.sequence_length]
        y = self.data[idx + self.sequence_length:idx + self.sequence_length + self.horizon]

        return torch.FloatTensor(x), torch.FloatTensor(y)


class LSTMModel(nn.Module):
    """LSTM neural network for time series forecasting."""

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 1
    ):
        """
        Initialize LSTM model.

        Args:
            input_size: Number of input features
            hidden_size: Hidden layer size
            num_layers: Number of LSTM layers
            dropout: Dropout probability
            output_size: Number of output features
        """
        super(LSTMModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )

        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch, seq_len, input_size)

        Returns:
            Output tensor
        """
        # LSTM forward
        lstm_out, _ = self.lstm(x)

        # Take the last time step
        last_time_step = lstm_out[:, -1, :]

        # Fully connected layer
        output = self.fc(last_time_step)

        return output


class LSTMForecaster:
    """
    LSTM-based time series forecaster.
    """

    def __init__(
        self,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        sequence_length: int = 30,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        epochs: int = 100,
        device: Optional[str] = None
    ):
        """
        Initialize LSTM forecaster.

        Args:
            hidden_size: LSTM hidden size
            num_layers: Number of LSTM layers
            dropout: Dropout probability
            sequence_length: Input sequence length
            learning_rate: Learning rate
            batch_size: Batch size for training
            epochs: Number of training epochs
            device: Device to use ('cuda' or 'cpu')
        """
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.sequence_length = sequence_length
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs

        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)

        # Model and scaler
        self.model = None
        self.scaler = StandardScaler()
        self.train_losses = []

        logger.info(f"Initialized LSTM forecaster on {self.device}")

    def fit(
        self,
        data: Union[pd.Series, np.ndarray],
        validation_split: float = 0.2,
        verbose: bool = True
    ) -> 'LSTMForecaster':
        """
        Train the LSTM model.

        Args:
            data: Training data
            validation_split: Fraction of data to use for validation
            verbose: Whether to print training progress

        Returns:
            self: Fitted model
        """
        logger.info(f"Training LSTM on {len(data)} observations")

        if isinstance(data, pd.Series):
            data = data.values

        # Reshape for scaling
        data_reshaped = data.reshape(-1, 1)

        # Scale data
        data_scaled = self.scaler.fit_transform(data_reshaped).flatten()

        # Create dataset
        dataset = TimeSeriesDataset(
            data_scaled,
            sequence_length=self.sequence_length,
            horizon=1
        )

        # Split into train/val
        val_size = int(len(dataset) * validation_split)
        train_size = len(dataset) - val_size

        train_dataset, val_dataset = torch.utils.data.random_split(
            dataset,
            [train_size, val_size]
        )

        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False
        )

        # Initialize model
        self.model = LSTMModel(
            input_size=1,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
            output_size=1
        ).to(self.device)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Training loop
        best_val_loss = float('inf')

        for epoch in range(self.epochs):
            # Training
            self.model.train()
            train_loss = 0.0

            for batch_x, batch_y in train_loader:
                batch_x = batch_x.unsqueeze(-1).to(self.device)
                batch_y = batch_y.to(self.device)

                # Forward pass
                optimizer.zero_grad()
                outputs = self.model(batch_x)
                loss = criterion(outputs, batch_y)

                # Backward pass
                loss.backward()
                optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)
            self.train_losses.append(train_loss)

            # Validation
            self.model.eval()
            val_loss = 0.0

            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x = batch_x.unsqueeze(-1).to(self.device)
                    batch_y = batch_y.to(self.device)

                    outputs = self.model(batch_x)
                    loss = criterion(outputs, batch_y)

                    val_loss += loss.item()

            val_loss /= len(val_loader)

            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss

            # Print progress
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{self.epochs}], Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")

        logger.info(f"Training completed. Best val loss: {best_val_loss:.6f}")

        return self

    def predict(
        self,
        data: Union[pd.Series, np.ndarray],
        steps: int = 1
    ) -> np.ndarray:
        """
        Generate forecasts.

        Args:
            data: Historical data (at least sequence_length points)
            steps: Number of steps to forecast

        Returns:
            Array of predictions
        """
        if self.model is None:
            raise ValueError("Model must be trained before prediction")

        logger.info(f"Generating {steps}-step forecast")

        if isinstance(data, pd.Series):
            data = data.values

        # Use last sequence_length points
        if len(data) > self.sequence_length:
            data = data[-self.sequence_length:]

        # Scale
        data_scaled = self.scaler.transform(data.reshape(-1, 1)).flatten()

        predictions = []
        current_sequence = data_scaled.copy()

        self.model.eval()
        with torch.no_grad():
            for _ in range(steps):
                # Prepare input
                x = torch.FloatTensor(current_sequence[-self.sequence_length:])
                x = x.unsqueeze(0).unsqueeze(-1).to(self.device)

                # Predict
                pred = self.model(x).cpu().numpy()[0, 0]
                predictions.append(pred)

                # Update sequence
                current_sequence = np.append(current_sequence, pred)

        # Inverse transform
        predictions = np.array(predictions).reshape(-1, 1)
        predictions = self.scaler.inverse_transform(predictions).flatten()

        return predictions

    def save(self, path: str):
        """Save model weights."""
        if self.model is None:
            raise ValueError("No model to save")

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler_mean': self.scaler.mean_,
            'scaler_scale': self.scaler.scale_
        }, path)

        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model weights."""
        checkpoint = torch.load(path)

        # Initialize model
        self.model = LSTMModel(
            input_size=1,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
            output_size=1
        ).to(self.device)

        # Load weights
        self.model.load_state_dict(checkpoint['model_state_dict'])

        # Load scaler parameters
        self.scaler.mean_ = checkpoint['scaler_mean']
        self.scaler.scale_ = checkpoint['scaler_scale']

        logger.info(f"Model loaded from {path}")


def main():
    """Example usage of LSTM forecaster."""
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=500, freq='D')

    trend = np.linspace(100, 150, 500)
    seasonality = 10 * np.sin(2 * np.pi * np.arange(500) / 7)
    noise = np.random.randn(500) * 3

    data = pd.Series(trend + seasonality + noise, index=dates)

    # Split
    train = data[:-30]
    test = data[-30:]

    print("=" * 60)
    print("LSTM Forecaster")
    print("=" * 60)

    # Train LSTM
    lstm = LSTMForecaster(
        hidden_size=64,
        num_layers=2,
        sequence_length=30,
        epochs=50,
        batch_size=32
    )

    lstm.fit(train, verbose=True)

    # Predict
    predictions = lstm.predict(train, steps=30)

    # Evaluate
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    mae = mean_absolute_error(test, predictions)
    rmse = np.sqrt(mean_squared_error(test, predictions))

    print(f"\nMAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")

    print("\nLSTM model trained and evaluated successfully!")


if __name__ == "__main__":
    main()

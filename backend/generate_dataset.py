"""
Synthetic sonar dataset generator for testing
Generates labeled sonar-like signals for training
"""
import numpy as np
import pandas as pd
from scipy import signal
import os
from utils import extract_features

class SyntheticSonarGenerator:
    """Generate synthetic sonar signals for different object types"""
    
    def __init__(self, sr=22050, duration=2.0):
        self.sr = sr
        self.duration = duration
        self.n_samples = int(sr * duration)
    
    def generate_torpedo_signal(self) -> np.ndarray:
        """
        Generate torpedo-like sonar signal
        Characteristics: High-frequency chirp with propeller modulation
        """
        t = np.linspace(0, self.duration, self.n_samples)
        
        
        chirp = signal.chirp(t, f0=2000, f1=5000, t1=self.duration, method='linear')
        
        
        modulation = 1 + 0.3 * np.sin(2 * np.pi * 40 * t)
        
       
        sig = chirp * modulation
        
        
        doppler = 1 + 0.1 * t / self.duration
        sig = sig * doppler
        
        
        noise = np.random.normal(0, 0.05, self.n_samples)
        sig = sig + noise
        
        
        sig = sig / np.max(np.abs(sig))
        
        return sig
    
    def generate_submarine_signal(self) -> np.ndarray:
        """
        Generate submarine-like sonar signal
        Characteristics: Low-frequency rumble with harmonics
        """
        t = np.linspace(0, self.duration, self.n_samples)
        
        
        base_freq = 100 + np.random.uniform(-20, 20)
        sig = np.sin(2 * np.pi * base_freq * t)
        
        
        for harmonic in [2, 3, 4, 5]:
            amplitude = 1.0 / harmonic
            sig += amplitude * np.sin(2 * np.pi * base_freq * harmonic * t)
        
        
        cavitation = signal.butter(4, [500, 3000], btype='band', fs=self.sr, output='sos')
        noise = np.random.normal(0, 0.3, self.n_samples)
        cavitation_noise = signal.sosfilt(cavitation, noise)
        
        sig = sig + 0.4 * cavitation_noise
        
        modulation = 1 + 0.2 * np.sin(2 * np.pi * 0.5 * t)
        sig = sig * modulation
        
        
        sig = sig / np.max(np.abs(sig))
        
        return sig
    
    def generate_fish_signal(self) -> np.ndarray:
        """
        Generate fish-like sonar signal
        Characteristics: Irregular, short bursts, mid-frequency
        """
        t = np.linspace(0, self.duration, self.n_samples)
        sig = np.zeros(self.n_samples)
        
        
        n_bursts = np.random.randint(5, 15)
        for _ in range(n_bursts):
            burst_start = np.random.randint(0, self.n_samples - 1000)
            burst_length = np.random.randint(200, 1000)
            
            if burst_start + burst_length < self.n_samples:
                
                burst_t = np.linspace(0, burst_length/self.sr, burst_length)
                freq = np.random.uniform(800, 2000)
                burst = np.sin(2 * np.pi * freq * burst_t)
                
                
                envelope = signal.windows.hann(burst_length)
                burst = burst * envelope
                
                
                sig[burst_start:burst_start+burst_length] += burst * np.random.uniform(0.3, 0.8)
        
        
        noise = np.random.normal(0, 0.1, self.n_samples)
        sig = sig + noise
        
        sig = sig / (np.max(np.abs(sig)) + 1e-8)
        
        return sig
    
    def generate_rock_signal(self) -> np.ndarray:
        """
        Generate rock-like sonar signal
        Characteristics: Sharp echo with decay
        """
        t = np.linspace(0, self.duration, self.n_samples)
        sig = np.zeros(self.n_samples)
        
        impulse_pos = int(0.3 * self.n_samples)
        impulse_width = 100
        
        
        impulse = signal.windows.gaussian(impulse_width, std=10)
        sig[impulse_pos:impulse_pos+impulse_width] = impulse
        
        for i in range(1, 4):
            echo_pos = impulse_pos + i * 5000
            echo_amplitude = 0.5 ** i
            if echo_pos + impulse_width < self.n_samples:
                sig[echo_pos:echo_pos+impulse_width] += impulse * echo_amplitude
        
        
        freq = np.random.uniform(1500, 4000)
        carrier = np.sin(2 * np.pi * freq * t)
        sig = sig * carrier
        
        
        decay = np.exp(-2 * t)
        sig = sig * decay
        
        
        noise = np.random.normal(0, 0.05, self.n_samples)
        sig = sig + noise
        
        
        sig = sig / (np.max(np.abs(sig)) + 1e-8)
        
        return sig
    
    def generate_unknown_signal(self) -> np.ndarray:
        """
        Generate unknown/anomalous sonar signal
        Characteristics: Random patterns, mixed frequencies
        """
        t = np.linspace(0, self.duration, self.n_samples)
        
        
        sig = np.zeros(self.n_samples)
        
        
        n_components = np.random.randint(3, 8)
        for _ in range(n_components):
            freq = np.random.uniform(200, 6000)
            phase = np.random.uniform(0, 2*np.pi)
            amplitude = np.random.uniform(0.2, 1.0)
            sig += amplitude * np.sin(2 * np.pi * freq * t + phase)
        
        
        mod_freq = np.random.uniform(1, 10)
        modulation = 1 + 0.5 * np.sin(2 * np.pi * mod_freq * t)
        sig = sig * modulation
        
        
        noise = np.random.normal(0, 0.3, self.n_samples)
        b, a = signal.butter(2, 0.1)
        colored_noise = signal.filtfilt(b, a, noise)
        sig = sig + colored_noise
        
        
        sig = sig / np.max(np.abs(sig))
        
        return sig
    
    def generate_dataset(self, n_samples_per_class=50, output_path='data/sonar_data.csv'):
        """
        Generate complete synthetic dataset
        
        Args:
            n_samples_per_class: Number of samples to generate for each class
            output_path: Path to save the dataset CSV
        """
        print(f"Generating synthetic sonar dataset...")
        print(f"Samples per class: {n_samples_per_class}")
        
        classes = ['Torpedo', 'Submarine', 'Fish', 'Rock', 'Unknown']
        generators = {
            'Torpedo': self.generate_torpedo_signal,
            'Submarine': self.generate_submarine_signal,
            'Fish': self.generate_fish_signal,
            'Rock': self.generate_rock_signal,
            'Unknown': self.generate_unknown_signal
        }
        
        all_features = []
        all_labels = []
        
        for class_name in classes:
            print(f"Generating {class_name} signals...")
            generator = generators[class_name]
            
            for i in range(n_samples_per_class):
                sig = generator()
                features = extract_features(sig, sr=self.sr)
                
                all_features.append(features)
                all_labels.append(class_name)
                
                if (i + 1) % 10 == 0:
                    print(f"  Generated {i + 1}/{n_samples_per_class}")
        
        df = pd.DataFrame(all_features)
        df['label'] = all_labels
        
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"\nDataset generated successfully!")
        print(f"  Total samples: {len(all_labels)}")
        print(f"  Features: {len(all_features[0])}")
        print(f"  Saved to: {output_path}")
        
        return df

def main():
    """Generate the synthetic dataset"""
    generator = SyntheticSonarGenerator()
    generator.generate_dataset(n_samples_per_class=50)

if __name__ == "__main__":
    main()

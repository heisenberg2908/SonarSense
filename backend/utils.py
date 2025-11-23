"""
Utility functions for audio preprocessing and feature extraction
"""
import numpy as np
import librosa
import soundfile as sf
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq
from typing import Union, Tuple
import io

def preprocess_signal(signal_data: np.ndarray, sr: int = 22050) -> np.ndarray:
    """
    Preprocess sonar signal with noise reduction and normalization
    
    Args:
        signal_data: Input signal array
        sr: Sample rate
    
    Returns:
        Preprocessed signal
    """
    detrended = scipy_signal.detrend(signal_data)
    
    
    sos = scipy_signal.butter(4, [100, 8000], btype='band', fs=sr, output='sos')
    filtered = scipy_signal.sosfilt(sos, detrended)
    
    normalized = filtered / (np.max(np.abs(filtered)) + 1e-8)
    
    return normalized

def extract_sonar_features(signal_data: np.ndarray, sr: int = 22050) -> np.ndarray:
    """
    Extract sonar-specific features as specified in the project requirements
    
    Features extracted:
    - Mean
    - Standard deviation
    - Peak amplitude
    - Signal energy
    - Spectral centroid
    - Top 3 FFT magnitudes
    - Additional frequency-domain features
    
    Args:
        signal_data: Preprocessed signal array
        sr: Sample rate
    
    Returns:
        Feature vector as numpy array
    """
    features = []
    
    
    features.append(np.mean(signal_data))              
    features.append(np.std(signal_data))               
    features.append(np.max(np.abs(signal_data)))       
    features.append(np.sum(signal_data ** 2))         
    
    n = len(signal_data)
    yf = fft(signal_data)
    magnitude = np.abs(yf[:n//2])
    freqs = fftfreq(n, 1/sr)[:n//2]
    
    spectral_centroid = np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-8)
    features.append(spectral_centroid)
    
    
    top_3_indices = np.argsort(magnitude)[-3:][::-1]
    top_3_magnitudes = magnitude[top_3_indices]
    features.extend(top_3_magnitudes.tolist())
    
    
    features.append(np.mean(magnitude))                
    features.append(np.std(magnitude))                 
    features.append(np.median(magnitude))              
    
   
    spectral_bandwidth = np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * magnitude) / (np.sum(magnitude) + 1e-8))
    features.append(spectral_bandwidth)
    
    
    cumsum = np.cumsum(magnitude)
    rolloff_idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
    spectral_rolloff = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0
    features.append(spectral_rolloff)
    
    return np.array(features)

def preprocess_audio(audio_data: Union[str, bytes, np.ndarray], 
                     sr: int = 22050, 
                     duration: float = None) -> Tuple[np.ndarray, int]:
    """
    Preprocess audio data
    
    Args:
        audio_data: Path to audio file, bytes, or numpy array
        sr: Target sample rate
        duration: Duration to load (in seconds)
    
    Returns:
        Preprocessed audio signal and sample rate
    """
    if isinstance(audio_data, str):
        
        y, current_sr = librosa.load(audio_data, sr=sr, duration=duration)
    elif isinstance(audio_data, bytes):
        
        y, current_sr = sf.read(io.BytesIO(audio_data))
        if current_sr != sr:
            y = librosa.resample(y, orig_sr=current_sr, target_sr=sr)
    elif isinstance(audio_data, np.ndarray):
        y = audio_data
        current_sr = sr
    else:
        raise ValueError("Unsupported audio_data type")
    
    
    y = preprocess_signal(y, sr)
    
    return y, sr

def extract_features(audio_data: Union[str, bytes, np.ndarray], 
                     sr: int = 22050,
                     n_mfcc: int = 13,
                     n_chroma: int = 12) -> np.ndarray:
    """
    Extract comprehensive audio features for classification
    
    Features extracted:
    - Sonar-specific features (mean, std, peak, energy, spectral features, FFT)
    - MFCCs (Mel-frequency cepstral coefficients)
    - Chroma features
    - Spectral contrast
    - Zero crossing rate
    - RMS energy
    
    Args:
        audio_data: Audio data to process
        sr: Sample rate
        n_mfcc: Number of MFCCs to extract
        n_chroma: Number of chroma features to extract
    
    Returns:
        Feature vector as numpy array
    """
    
    y, sr = preprocess_audio(audio_data, sr=sr)
    
  
    sonar_features = extract_sonar_features(y, sr)
    
    features = [sonar_features]
    
    
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    features.extend([
        np.mean(mfccs, axis=1),
        np.std(mfccs, axis=1),
    ])
    
    
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=n_chroma)
    features.extend([
        np.mean(chroma, axis=1),
        np.std(chroma, axis=1)
    ])
    
    
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    features.extend([
        np.mean(contrast, axis=1),
    ])
    
    
    zcr = librosa.feature.zero_crossing_rate(y)
    features.append([
        np.mean(zcr),
        np.std(zcr)
    ])
    
   
    rms = librosa.feature.rms(y=y)
    features.append([
        np.mean(rms),
        np.std(rms),
    ])
    
    
    feature_vector = np.concatenate([np.array(f).flatten() for f in features])
    
    return feature_vector

def get_waveform_data(audio_data: Union[str, bytes, np.ndarray], 
                      sr: int = 22050) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get waveform data for visualization
    
    Returns:
        time array, amplitude array
    """
    y, sr = preprocess_audio(audio_data, sr=sr)
    time = np.linspace(0, len(y) / sr, len(y))
    return time, y

def get_frequency_spectrum(audio_data: Union[str, bytes, np.ndarray],
                          sr: int = 22050) -> Tuple[np.ndarray, np.ndarray]:
    """
    Get frequency spectrum for visualization
    
    Returns:
        frequency array, magnitude array
    """
    y, sr = preprocess_audio(audio_data, sr=sr)
    
    n = len(y)
    yf = fft(y)
    magnitude = np.abs(yf[:n//2])
    freqs = fftfreq(n, 1/sr)[:n//2]
    
    return freqs, magnitude

def extract_spectral_features(audio_data: Union[str, bytes, np.ndarray],
                               sr: int = 22050) -> dict:
    """
    Extract detailed spectral features for analysis
    
    Returns:
        Dictionary of spectral features
    """
    y, sr = preprocess_audio(audio_data, sr=sr)
    
   
    S = np.abs(librosa.stft(y))
    
    features = {
        'spectral_centroid': np.mean(librosa.feature.spectral_centroid(S=S, sr=sr)),
        'spectral_bandwidth': np.mean(librosa.feature.spectral_bandwidth(S=S, sr=sr)),
        'spectral_rolloff': np.mean(librosa.feature.spectral_rolloff(S=S, sr=sr)),
        'spectral_flatness': np.mean(librosa.feature.spectral_flatness(S=S)),
        'zero_crossing_rate': np.mean(librosa.feature.zero_crossing_rate(y)),
        'rms_energy': np.mean(librosa.feature.rms(S=S)),
    }
    
    return features

def calculate_mel_spectrogram(audio_data: Union[str, bytes, np.ndarray],
                               sr: int = 22050,
                               n_mels: int = 128) -> np.ndarray:
    """
    Calculate mel spectrogram for visualization or deep learning
    
    Returns:
        Mel spectrogram as 2D numpy array
    """
    y, sr = preprocess_audio(audio_data, sr=sr)
    
    mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    
    return mel_spec_db
from pydub import AudioSegment
import os

def process_audio(input_path, output_path, mode, percentage):
    """
    Process audio based on mode and intensity.
    Uses frame-rate override for stable speed/pitch change.
    Exports both MP3 and WAV formats.
    Returns tuple (success, output_filename_base).
    """
    try:
        audio = AudioSegment.from_file(input_path)

        # No effect at 0%
        if percentage == 0:
            # Export MP3
            mp3_path = output_path.replace('.mp3', '_output.mp3') if not output_path.endswith('_output.mp3') else output_path
            audio.export(mp3_path, format="mp3")
            # Export WAV
            wav_path = mp3_path.replace('_output.mp3', '_output.wav')
            audio.export(wav_path, format="wav")
            return True

        # Calculate speed factor
        if mode == 'slow':
            # 0% -> 1.0x (original)
            # 100% -> 0.7x (slowed)
            factor = 1.0 - (percentage / 100.0 * 0.3)
        else:  # speed
            # 0% -> 1.0x (original)
            # 100% -> 1.5x (sped up)
            factor = 1.0 + (percentage / 100.0 * 0.5)

        # Apply speed/pitch change
        new_frame_rate = int(audio.frame_rate * factor)
        new_audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
        new_audio = new_audio.set_frame_rate(audio.frame_rate)

        # Export MP3
        mp3_path = output_path.replace('.mp3', '_output.mp3') if not output_path.endswith('_output.mp3') else output_path
        new_audio.export(mp3_path, format="mp3")
        
        # Export WAV
        wav_path = mp3_path.replace('_output.mp3', '_output.wav')
        new_audio.export(wav_path, format="wav")
        
        return True

    except Exception as e:
        return False

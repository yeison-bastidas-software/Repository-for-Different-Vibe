from pydub import AudioSegment
import os

def process_audio(input_path, output_path, mode, percentage):
    """
    Process audio based on mode and intensity.
    Uses frame-rate override for stable speed/pitch change.
    """
    try:
        audio = AudioSegment.from_mp3(input_path)

        # No effect at 0%
        if percentage == 0:
            audio.export(output_path, format="mp3")
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

        # Export result
        new_audio.export(output_path, format="mp3")
        return True

    except Exception as e:
        return False

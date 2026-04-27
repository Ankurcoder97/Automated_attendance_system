from resemblyzer import VoiceEncoder,preprocess_wav
import numpy as np
import io
import librosa
import streamlit as st


@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()

def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()

        audio,sr = librosa.load(io.BytesIO(audio_bytes),sr=16000)
        wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()
    except Exception as e:
        st.error('Voice recg Error')
        return None
    

def identify_speaker(new_embedding,candidates_dict,thresold=0.65):
    if new_embedding is None or not candidates_dict:
        return None,0.0
    
    best_sid = None
    best_score = -1.0

    for sid,stored_embedding in  candidates_dict.items():
        if stored_embedding:
            similarity = np.dot(new_embedding,stored_embedding)
            if similarity>best_score:
                best_score=similarity
                best_sid = sid

        if best_score>=thresold:
            return best_sid,best_score

        return None,best_score


def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65):
    try:
        encoder = load_voice_encoder()

        # ✅ Load audio safely
        audio_stream = io.BytesIO(audio_bytes)
        audio, sr = librosa.load(audio_stream, sr=16000)

        if len(audio) == 0:
            raise ValueError("Audio is empty")

        # ✅ Split into speech segments
        segments = librosa.effects.split(audio, top_db=30)

        identified_result = {}

        for start, end in segments:

            # ✅ Ignore very small segments
            if (end - start) < sr * 0.5:
                continue

            segment_audio = audio[start:end]

            try:
                wav = preprocess_wav(segment_audio)
                embedding = encoder.embed_utterance(wav)

                sid, score = identify_speaker(
                    embedding,
                    candidates_dict,
                    threshold
                )

                # ✅ FIXED BUG HERE
                if sid:
                    if (
                        sid not in identified_result
                        or score > identified_result[sid]
                    ):
                        identified_result[sid] = float(score)

            except Exception as inner_error:
                print("Segment error:", inner_error)
                continue

        return identified_result

    except Exception as e:
        # ✅ Show real error (VERY IMPORTANT)
        st.error(f"Bulk process error: {str(e)}")
        print("FULL ERROR:", e)
        return {}
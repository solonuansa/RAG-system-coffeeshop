def patch_instagrapi():
    """Patch instagrapi untuk handle audio_filter_infos = None"""
    try:
        from instagrapi import types

        # Simpan validator asli
        original_validator = (
            types.Media.__pydantic_model__.model_validate
            if hasattr(types.Media, "__pydantic_model__")
            else None
        )

        # Monkey patch untuk pre-process data
        original_init = types.Media.__init__

        def patched_init(self, **data):
            # Fix clips_metadata
            if "clips_metadata" in data and data["clips_metadata"]:
                clips = data["clips_metadata"]

                # Fix original_sound_info
                if "original_sound_info" in clips and clips["original_sound_info"]:
                    sound_info = clips["original_sound_info"]
                    if (
                        "audio_filter_infos" in sound_info
                        and sound_info["audio_filter_infos"] is None
                    ):
                        sound_info["audio_filter_infos"] = []

                # Fix music_info jika ada
                if "music_info" in clips and clips["music_info"]:
                    music_info = clips["music_info"]
                    if (
                        "audio_filter_infos" in music_info
                        and music_info["audio_filter_infos"] is None
                    ):
                        music_info["audio_filter_infos"] = []

                # Fix mashup_info (Pydantic validation error)
                if "mashup_info" not in clips:
                    clips["mashup_info"] = {}

            return original_init(self, **data)

        types.Media.__init__ = patched_init
        print("✅ Instagrapi berhasil di-patch untuk handle Reels/Video")

    except Exception as e:
        print(f"⚠️  Gagal patch instagrapi: {e}")


# Jalankan patch saat import
patch_instagrapi()

from fastapi import APIRouter
from models import ConfigResponse, I18nResponse, ModelInfo
from config import AVAILABLE_MODELS, DEFAULT_MODEL, IMAGE_WIDTH, DEFAULT_NICK_NAME, DEFAULT_CHARACTER, USER_AVATAR, ASSISTANT_AVATAR
from i18n import get_texts

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=ConfigResponse)
def get_config():
    models = []
    for m in AVAILABLE_MODELS:
        t = m["type"]
        models.append(ModelInfo(
            id=m["id"],
            name=m["name"],
            type=t,
            provider=m["provider"],
            vision=(t == "vision"),
            image_output=(t == "image_gen"),
        ))
    return ConfigResponse(
        models=models,
        default_model=DEFAULT_MODEL,
        image_width=IMAGE_WIDTH,
        default_nick_name=DEFAULT_NICK_NAME,
        default_character=DEFAULT_CHARACTER,
        user_avatar=USER_AVATAR,
        assistant_avatar=ASSISTANT_AVATAR,
    )


@router.get("/i18n", response_model=I18nResponse)
def get_i18n(lang: str = "zh"):
    return I18nResponse(lang=lang, texts=get_texts(lang))

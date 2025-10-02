from fastapi import APIRouter, HTTPException, status, Depends
from app.models.config_site import ConfigSiteCreate, ConfigSiteUpdate
from app.models.user import PreferencesUpdate
from app.middleware.auth import get_current_user
from app.database import get_database
from bson import ObjectId
from datetime import datetime

router = APIRouter()


# Config Sites Endpoints
@router.get("/sites")
async def get_config_sites(
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    cursor = db.config_sites.find({"user_id": user_id})
    config_sites = await cursor.to_list(length=None)
    
    # Convertir ObjectId a string
    for site in config_sites:
        site["id"] = str(site.pop("_id"))
        site["user_id"] = str(site["user_id"])
    
    return {
        "success": True,
        "data": config_sites
    }


@router.post("/sites")
async def create_config_site(
    config: ConfigSiteCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Crear configuración
    config_dict = config.model_dump()
    config_dict["user_id"] = user_id
    config_dict["created_at"] = datetime.utcnow()
    config_dict["updated_at"] = datetime.utcnow()
    
    result = await db.config_sites.insert_one(config_dict)
    
    config_dict["id"] = str(result.inserted_id)
    config_dict["user_id"] = str(config_dict["user_id"])
    
    return {
        "success": True,
        "data": config_dict
    }


@router.put("/sites/{site_id}")
async def update_config_site(
    site_id: str,
    updates: ConfigSiteUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Preparar actualizaciones
    update_dict = {}
    if updates.name is not None:
        update_dict["name"] = updates.name
    if updates.urlPattern is not None:
        update_dict["urlPattern"] = updates.urlPattern
    if updates.selectors is not None:
        update_dict["selectors"] = updates.selectors.model_dump()
    if updates.investment is not None:
        update_dict["investment"] = updates.investment
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay campos para actualizar"
        )
    
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db.config_sites.update_one(
        {"_id": ObjectId(site_id), "user_id": user_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    # Obtener configuración actualizada
    config_site = await db.config_sites.find_one({"_id": ObjectId(site_id)})
    config_site["id"] = str(config_site.pop("_id"))
    config_site["user_id"] = str(config_site["user_id"])
    
    return {
        "success": True,
        "data": config_site
    }


@router.delete("/sites/{site_id}")
async def delete_config_site(
    site_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    result = await db.config_sites.delete_one({
        "_id": ObjectId(site_id),
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    return {"success": True, "message": "Configuración eliminada"}


# User Preferences Endpoints
@router.get("/preferences")
async def get_preferences(
    current_user: dict = Depends(get_current_user)
):
    preferences = current_user.get("preferences", {})
    
    return {
        "success": True,
        "data": preferences
    }


@router.put("/preferences")
async def update_preferences(
    preferences: PreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Obtener preferencias actuales
    current_prefs = current_user.get("preferences", {})
    
    # Actualizar solo los campos proporcionados
    update_dict = {}
    if preferences.theme is not None:
        update_dict["preferences.theme"] = preferences.theme
    if preferences.autoReplication is not None:
        update_dict["preferences.autoReplication"] = preferences.autoReplication
    if preferences.manualRecordReferences is not None:
        update_dict["preferences.manualRecordReferences"] = preferences.manualRecordReferences
    
    if update_dict:
        await db.users.update_one(
            {"_id": user_id},
            {"$set": update_dict}
        )
    
    # Obtener usuario actualizado
    updated_user = await db.users.find_one({"_id": user_id})
    
    return {
        "success": True,
        "data": updated_user.get("preferences", {})
    }

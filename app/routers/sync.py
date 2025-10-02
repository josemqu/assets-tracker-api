from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.models.investment import InvestmentCreate
from app.models.config_site import ConfigSiteCreate
from app.middleware.auth import get_current_user
from app.database import get_database
from datetime import datetime

router = APIRouter()


class SyncPushRequest(BaseModel):
    investments: Optional[List[InvestmentCreate]] = []
    configSites: Optional[List[ConfigSiteCreate]] = []
    preferences: Optional[Dict[str, Any]] = None
    clientTimestamp: str


class ExportData(BaseModel):
    investments: Optional[List[Dict[str, Any]]] = []
    configSites: Optional[List[Dict[str, Any]]] = []
    preferences: Optional[Dict[str, Any]] = None


class ImportRequest(BaseModel):
    data: ExportData
    mode: str = "merge"  # "merge" or "replace"


@router.get("/status")
async def get_sync_status(
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Contar registros
    investment_count = await db.investments.count_documents({"user_id": user_id})
    config_count = await db.config_sites.count_documents({"user_id": user_id})
    
    # Obtener última actualización
    last_investment = await db.investments.find_one(
        {"user_id": user_id},
        sort=[("updated_at", -1)]
    )
    
    last_sync = None
    if last_investment and "updated_at" in last_investment:
        last_sync = last_investment["updated_at"].isoformat()
    
    return {
        "success": True,
        "data": {
            "lastSync": last_sync,
            "recordCount": investment_count,
            "configCount": config_count
        }
    }


@router.post("/push")
async def push_sync(
    sync_data: SyncPushRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    investments_created = 0
    investments_updated = 0
    configs_created = 0
    configs_updated = 0
    
    # Sincronizar inversiones
    if sync_data.investments:
        for investment in sync_data.investments:
            existing = await db.investments.find_one({
                "user_id": user_id,
                "timestamp": investment.timestamp,
                "entidad": investment.entidad
            })
            
            if existing:
                await db.investments.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$set": {
                            "monto_ars": investment.monto_ars,
                            "monto_usd": investment.monto_usd,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                investments_updated += 1
            else:
                investment_dict = investment.model_dump()
                investment_dict["user_id"] = user_id
                investment_dict["created_at"] = datetime.utcnow()
                investment_dict["updated_at"] = datetime.utcnow()
                await db.investments.insert_one(investment_dict)
                investments_created += 1
    
    # Sincronizar configuraciones de sitios
    if sync_data.configSites:
        for config in sync_data.configSites:
            # Buscar por nombre y urlPattern
            existing = await db.config_sites.find_one({
                "user_id": user_id,
                "name": config.name,
                "urlPattern": config.urlPattern
            })
            
            if existing:
                await db.config_sites.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$set": {
                            "selectors": config.selectors.model_dump(),
                            "investment": config.investment,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                configs_updated += 1
            else:
                config_dict = config.model_dump()
                config_dict["user_id"] = user_id
                config_dict["created_at"] = datetime.utcnow()
                config_dict["updated_at"] = datetime.utcnow()
                await db.config_sites.insert_one(config_dict)
                configs_created += 1
    
    # Actualizar preferencias si se proporcionan
    if sync_data.preferences:
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"preferences": sync_data.preferences}}
        )
    
    return {
        "success": True,
        "synced": {
            "investments": {
                "created": investments_created,
                "updated": investments_updated
            },
            "configSites": {
                "created": configs_created,
                "updated": configs_updated
            }
        },
        "serverTimestamp": datetime.utcnow().isoformat()
    }


@router.get("/pull")
async def pull_sync(
    since: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Construir filtro de fecha si se proporciona
    filter_query = {"user_id": user_id}
    if since:
        since_date = datetime.fromtimestamp(since / 1000)
        filter_query["updated_at"] = {"$gte": since_date}
    
    # Obtener inversiones
    cursor = db.investments.find(filter_query).sort("updated_at", -1)
    investments = await cursor.to_list(length=None)
    
    for inv in investments:
        inv["id"] = str(inv.pop("_id"))
        inv["user_id"] = str(inv["user_id"])
        # Convertir fechas a ISO string
        if "created_at" in inv:
            inv["created_at"] = inv["created_at"].isoformat()
        if "updated_at" in inv:
            inv["updated_at"] = inv["updated_at"].isoformat()
    
    # Obtener configuraciones de sitios
    config_filter = {"user_id": user_id}
    if since:
        config_filter["updated_at"] = {"$gte": since_date}
    
    cursor = db.config_sites.find(config_filter).sort("updated_at", -1)
    config_sites = await cursor.to_list(length=None)
    
    for site in config_sites:
        site["id"] = str(site.pop("_id"))
        site["user_id"] = str(site["user_id"])
        if "created_at" in site:
            site["created_at"] = site["created_at"].isoformat()
        if "updated_at" in site:
            site["updated_at"] = site["updated_at"].isoformat()
    
    # Obtener preferencias
    preferences = current_user.get("preferences", {})
    
    return {
        "success": True,
        "data": {
            "investments": investments,
            "configSites": config_sites,
            "preferences": preferences,
            "deletedInvestments": [],  # TODO: Implementar tracking de eliminados
            "deletedConfigSites": []
        },
        "serverTimestamp": datetime.utcnow().isoformat()
    }


@router.get("/export")
async def export_data(
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Obtener todas las inversiones
    cursor = db.investments.find({"user_id": user_id}).sort("timestamp", -1)
    investments = await cursor.to_list(length=None)
    
    for inv in investments:
        inv["id"] = str(inv.pop("_id"))
        inv["user_id"] = str(inv["user_id"])
        if "created_at" in inv:
            inv["created_at"] = inv["created_at"].isoformat()
        if "updated_at" in inv:
            inv["updated_at"] = inv["updated_at"].isoformat()
    
    # Obtener todas las configuraciones
    cursor = db.config_sites.find({"user_id": user_id})
    config_sites = await cursor.to_list(length=None)
    
    for site in config_sites:
        site["id"] = str(site.pop("_id"))
        site["user_id"] = str(site["user_id"])
        if "created_at" in site:
            site["created_at"] = site["created_at"].isoformat()
        if "updated_at" in site:
            site["updated_at"] = site["updated_at"].isoformat()
    
    # Obtener preferencias
    preferences = current_user.get("preferences", {})
    
    return {
        "version": "1.0",
        "exportDate": datetime.utcnow().isoformat(),
        "user": {
            "email": current_user.get("email")
        },
        "data": {
            "investments": investments,
            "configSites": config_sites,
            "preferences": preferences
        }
    }


@router.post("/import")
async def import_data(
    import_request: ImportRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    investments_imported = 0
    configs_imported = 0
    
    # Si el modo es "replace", eliminar datos existentes
    if import_request.mode == "replace":
        await db.investments.delete_many({"user_id": user_id})
        await db.config_sites.delete_many({"user_id": user_id})
    
    # Importar inversiones
    if import_request.data.investments:
        for inv_data in import_request.data.investments:
            # Remover campos internos si existen
            inv_data.pop("id", None)
            inv_data.pop("_id", None)
            inv_data.pop("user_id", None)
            
            # Si es merge, verificar si existe
            if import_request.mode == "merge":
                existing = await db.investments.find_one({
                    "user_id": user_id,
                    "timestamp": inv_data.get("timestamp"),
                    "entidad": inv_data.get("entidad")
                })
                
                if existing:
                    continue  # Ya existe, saltar
            
            # Insertar
            inv_data["user_id"] = user_id
            inv_data["created_at"] = datetime.utcnow()
            inv_data["updated_at"] = datetime.utcnow()
            await db.investments.insert_one(inv_data)
            investments_imported += 1
    
    # Importar configuraciones
    if import_request.data.configSites:
        for config_data in import_request.data.configSites:
            # Remover campos internos
            config_data.pop("id", None)
            config_data.pop("_id", None)
            config_data.pop("user_id", None)
            
            # Si es merge, verificar si existe
            if import_request.mode == "merge":
                existing = await db.config_sites.find_one({
                    "user_id": user_id,
                    "name": config_data.get("name"),
                    "urlPattern": config_data.get("urlPattern")
                })
                
                if existing:
                    continue  # Ya existe, saltar
            
            # Insertar
            config_data["user_id"] = user_id
            config_data["created_at"] = datetime.utcnow()
            config_data["updated_at"] = datetime.utcnow()
            await db.config_sites.insert_one(config_data)
            configs_imported += 1
    
    # Importar preferencias (siempre reemplaza)
    if import_request.data.preferences:
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"preferences": import_request.data.preferences}}
        )
    
    return {
        "success": True,
        "imported": {
            "investments": investments_imported,
            "configSites": configs_imported
        }
    }

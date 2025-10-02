from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.models.investment import InvestmentCreate, InvestmentUpdate, BulkInvestmentRequest
from app.middleware.auth import get_current_user
from app.database import get_database
from bson import ObjectId
from datetime import datetime

router = APIRouter()


@router.get("/")
async def get_investments(
    entity: Optional[str] = None,
    dateFrom: Optional[int] = None,
    dateTo: Optional[int] = None,
    limit: int = Query(1000, le=1000),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Construir filtro
    filter_query = {"user_id": user_id}
    
    if entity:
        filter_query["entidad"] = entity
    
    if dateFrom or dateTo:
        filter_query["timestamp"] = {}
        if dateFrom:
            filter_query["timestamp"]["$gte"] = dateFrom
        if dateTo:
            filter_query["timestamp"]["$lte"] = dateTo
    
    # Consultar
    cursor = db.investments.find(filter_query).sort("timestamp", -1).skip(offset).limit(limit)
    investments = await cursor.to_list(length=limit)
    
    total = await db.investments.count_documents(filter_query)
    
    # Convertir ObjectId a string
    for inv in investments:
        inv["id"] = str(inv.pop("_id"))
        inv["user_id"] = str(inv["user_id"])
    
    return {
        "success": True,
        "data": investments,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "hasMore": total > offset + len(investments)
        }
    }


@router.post("/")
async def create_investment(
    investment: InvestmentCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Verificar si existe
    existing = await db.investments.find_one({
        "user_id": user_id,
        "timestamp": investment.timestamp,
        "entidad": investment.entidad
    })
    
    if existing:
        # Actualizar
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
        return {
            "success": True,
            "data": {"id": str(existing["_id"])},
            "isUpdate": True
        }
    
    # Crear nuevo
    investment_dict = investment.model_dump()
    investment_dict["user_id"] = user_id
    investment_dict["created_at"] = datetime.utcnow()
    investment_dict["updated_at"] = datetime.utcnow()
    
    result = await db.investments.insert_one(investment_dict)
    
    return {
        "success": True,
        "data": {"id": str(result.inserted_id)},
        "isUpdate": False
    }


@router.post("/bulk")
async def bulk_create_investments(
    bulk_request: BulkInvestmentRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    created = 0
    updated = 0
    failed = 0
    
    for investment in bulk_request.records:
        try:
            # Verificar si existe
            existing = await db.investments.find_one({
                "user_id": user_id,
                "timestamp": investment.timestamp,
                "entidad": investment.entidad
            })
            
            if existing:
                # Actualizar
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
                updated += 1
            else:
                # Crear nuevo
                investment_dict = investment.model_dump()
                investment_dict["user_id"] = user_id
                investment_dict["created_at"] = datetime.utcnow()
                investment_dict["updated_at"] = datetime.utcnow()
                
                await db.investments.insert_one(investment_dict)
                created += 1
        except Exception as e:
            print(f"Error processing investment: {e}")
            failed += 1
    
    return {
        "success": True,
        "summary": {
            "total": len(bulk_request.records),
            "created": created,
            "updated": updated,
            "failed": failed
        }
    }


@router.put("/{investment_id}")
async def update_investment(
    investment_id: str,
    updates: InvestmentUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    # Preparar actualizaciones
    update_dict = {}
    if updates.monto_ars is not None:
        update_dict["monto_ars"] = updates.monto_ars
    if updates.monto_usd is not None:
        update_dict["monto_usd"] = updates.monto_usd
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay campos para actualizar"
        )
    
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await db.investments.update_one(
        {"_id": ObjectId(investment_id), "user_id": user_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro no encontrado"
        )
    
    # Obtener registro actualizado
    investment = await db.investments.find_one({"_id": ObjectId(investment_id)})
    investment["id"] = str(investment.pop("_id"))
    investment["user_id"] = str(investment["user_id"])
    
    return {
        "success": True,
        "data": investment
    }


@router.delete("/{investment_id}")
async def delete_investment(
    investment_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    result = await db.investments.delete_one({
        "_id": ObjectId(investment_id),
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro no encontrado"
        )
    
    return {"success": True, "message": "Registro eliminado"}


@router.delete("/")
async def delete_all_investments(
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user_id = current_user["_id"]
    
    result = await db.investments.delete_many({"user_id": user_id})
    
    return {
        "success": True,
        "deleted": result.deleted_count
    }

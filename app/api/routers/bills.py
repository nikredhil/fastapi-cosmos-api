"""Bills API router (nested under a building) — rent and utility charges."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.dependencies import get_bill_service
from app.core.security import get_current_user
from app.models.domain.enums import BillStatus, BillType
from app.models.schemas.bill import (
    Bill,
    BillCreate,
    BillUpdate,
    GenerateBillsRequest,
    PaymentCreate,
    RentStatusRequest,
)
from app.models.schemas.common import Page
from app.services.bill_service import BillNotFoundError, BillService
from app.services.building_service import BuildingNotFoundError

router = APIRouter(prefix="/buildings/{building_id}/bills", tags=["bills"])


def _building_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")


def _bill_404() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")


@router.post("", response_model=Bill, status_code=status.HTTP_201_CREATED)
async def create_bill(
    building_id: str,
    payload: BillCreate,
    user: str = Depends(get_current_user),
    service: BillService = Depends(get_bill_service),
) -> Bill:
    try:
        return await service.create(owner=user, building_id=building_id, payload=payload)
    except BuildingNotFoundError:
        raise _building_404()


@router.get("", response_model=Page[Bill])
async def list_bills(
    building_id: str,
    period: str | None = Query(default=None, description="Billing month, e.g. 2026-06"),
    status_filter: BillStatus | None = Query(default=None, alias="status"),
    bill_type: BillType | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    limit: int = Query(1000, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    user: str = Depends(get_current_user),
    service: BillService = Depends(get_bill_service),
) -> Page[Bill]:
    try:
        items = await service.list(
            owner=user,
            building_id=building_id,
            period=period,
            status=status_filter.value if status_filter else None,
            bill_type=bill_type.value if bill_type else None,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )
    except BuildingNotFoundError:
        raise _building_404()
    return Page[Bill](items=items, limit=limit, offset=offset, count=len(items))


@router.post("/generate", response_model=Page[Bill], status_code=status.HTTP_201_CREATED)
async def generate_bills(
    building_id: str,
    payload: GenerateBillsRequest,
    user: str = Depends(get_current_user),
    service: BillService = Depends(get_bill_service),
) -> Page[Bill]:
    try:
        items = await service.generate_monthly(owner=user, building_id=building_id, payload=payload)
    except BuildingNotFoundError:
        raise _building_404()
    return Page[Bill](items=items, limit=len(items), offset=0, count=len(items))


@router.post("/rent-status", response_model=Bill | None)
async def set_rent_status(
    building_id: str,
    payload: RentStatusRequest,
    user: str = Depends(get_current_user),
    service: BillService = Depends(get_bill_service),
) -> Bill | None:
    """Mark a tenant's rent for a month paid/unpaid (rent tracker grid)."""
    try:
        return await service.set_rent_status(
            owner=user,
            building_id=building_id,
            tenant_id=payload.tenant_id,
            period=payload.period,
            paid=payload.paid,
        )
    except BuildingNotFoundError:
        raise _building_404()


@router.patch("/{bill_id}", response_model=Bill)
async def update_bill(
    building_id: str,
    bill_id: str,
    payload: BillUpdate,
    user: str = Depends(get_current_user),
    service: BillService = Depends(get_bill_service),
) -> Bill:
    try:
        return await service.update(
            owner=user, building_id=building_id, bill_id=bill_id, payload=payload
        )
    except BuildingNotFoundError:
        raise _building_404()
    except BillNotFoundError:
        raise _bill_404()


@router.post("/{bill_id}/payments", response_model=Bill, status_code=status.HTTP_201_CREATED)
async def record_payment(
    building_id: str,
    bill_id: str,
    payload: PaymentCreate,
    user: str = Depends(get_current_user),
    service: BillService = Depends(get_bill_service),
) -> Bill:
    try:
        return await service.record_payment(
            owner=user, building_id=building_id, bill_id=bill_id, payload=payload
        )
    except BuildingNotFoundError:
        raise _building_404()
    except BillNotFoundError:
        raise _bill_404()


@router.delete(
    "/{bill_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_bill(
    building_id: str,
    bill_id: str,
    user: str = Depends(get_current_user),
    service: BillService = Depends(get_bill_service),
) -> Response:
    try:
        await service.delete(owner=user, building_id=building_id, bill_id=bill_id)
    except BuildingNotFoundError:
        raise _building_404()
    except BillNotFoundError:
        raise _bill_404()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

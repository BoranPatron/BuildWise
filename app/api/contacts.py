"""
Contacts API Endpoints
Verwaltet das Kontaktbuch für Bauträger und Dienstleister
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..core.database import get_db
from ..api.deps import get_current_user
from ..models import User, Contact
from ..schemas.contact import ContactCreate, ContactUpdate, ContactRead

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Erstellt einen neuen Kontakt im Kontaktbuch
    """
    # Prüfe ob Kontakt bereits existiert (gleicher service_provider_id für diesen User)
    if contact_data.service_provider_id:
        existing_query = select(Contact).where(
            and_(
                Contact.user_id == current_user.id,
                Contact.service_provider_id == contact_data.service_provider_id
            )
        )
        result = await db.execute(existing_query)
        existing_contact = result.scalar_one_or_none()
        
        if existing_contact:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dieser Kontakt existiert bereits in Ihrem Kontaktbuch"
            )
    
    # Fallback-Logik: Verwende contact_person wenn company_name leer ist
    final_company_name = contact_data.company_name
    if not final_company_name or final_company_name.strip() == "":
        if contact_data.contact_person:
            final_company_name = contact_data.contact_person
        else:
            final_company_name = "Unbekanntes Unternehmen"
    
    # Erstelle neuen Kontakt
    new_contact = Contact(
        user_id=current_user.id,
        company_name=final_company_name,
        contact_person=contact_data.contact_person,
        email=contact_data.email,
        phone=contact_data.phone,
        website=contact_data.website,
        category=contact_data.category,
        rating=contact_data.rating,
        notes=contact_data.notes,
        address_street=contact_data.address_street,
        address_city=contact_data.address_city,
        address_zip=contact_data.address_zip,
        address_country=contact_data.address_country or 'Deutschland',
        milestone_id=contact_data.milestone_id,
        project_id=contact_data.project_id,
        service_provider_id=contact_data.service_provider_id,
        favorite=contact_data.favorite or False
    )
    
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    
    return new_contact


@router.get("", response_model=List[ContactRead])
async def get_contacts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
    project_id: Optional[int] = None,
    favorite: Optional[bool] = None,
    search: Optional[str] = None
):
    """
    Holt alle Kontakte des aktuellen Benutzers mit optionalen Filtern
    """
    query = select(Contact).where(Contact.user_id == current_user.id)
    
    # Filter anwenden
    if category:
        query = query.where(Contact.category == category)
    
    if project_id:
        query = query.where(Contact.project_id == project_id)
    
    if favorite is not None:
        query = query.where(Contact.favorite == favorite)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Contact.company_name.ilike(search_pattern),
                Contact.contact_person.ilike(search_pattern),
                Contact.email.ilike(search_pattern)
            )
        )
    
    # Sortiere nach Favoriten und dann alphabetisch
    query = query.order_by(Contact.favorite.desc(), Contact.company_name)
    
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    return contacts


@router.get("/{contact_id}", response_model=ContactRead)
async def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Holt einen spezifischen Kontakt
    """
    query = select(Contact).where(
        and_(
            Contact.id == contact_id,
            Contact.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kontakt nicht gefunden"
        )
    
    return contact


@router.put("/{contact_id}", response_model=ContactRead)
async def update_contact(
    contact_id: int,
    contact_data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Aktualisiert einen Kontakt
    """
    query = select(Contact).where(
        and_(
            Contact.id == contact_id,
            Contact.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kontakt nicht gefunden"
        )
    
    # Update Felder
    update_data = contact_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)
    
    await db.commit()
    await db.refresh(contact)
    
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Löscht einen Kontakt
    """
    query = select(Contact).where(
        and_(
            Contact.id == contact_id,
            Contact.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kontakt nicht gefunden"
        )
    
    await db.delete(contact)
    await db.commit()
    
    return None


@router.post("/{contact_id}/favorite", response_model=ContactRead)
async def toggle_favorite(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Togglet den Favoriten-Status eines Kontakts
    """
    query = select(Contact).where(
        and_(
            Contact.id == contact_id,
            Contact.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kontakt nicht gefunden"
        )
    
    contact.favorite = not contact.favorite
    
    await db.commit()
    await db.refresh(contact)
    
    return contact


@router.get("/categories/list", response_model=List[str])
async def get_contact_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Holt alle verwendeten Kategorien aus den Kontakten des Benutzers
    """
    query = select(Contact.category).where(
        and_(
            Contact.user_id == current_user.id,
            Contact.category.isnot(None)
        )
    ).distinct()
    
    result = await db.execute(query)
    categories = [cat for cat in result.scalars().all() if cat]
    
    return categories


# Best Practice: Appointment Response System

## Problem
Die aktuelle Implementierung speichert Terminantworten als JSON-String in der `responses` Spalte der `appointments` Tabelle. Dies führt zu:
- Parsing-Problemen (Double-Encoding)
- Schlechter Performance
- Schwieriger Wartbarkeit
- Inkonsistenzen zwischen Frontend-Instanzen

## Lösung: Separate Response-Tabelle

### 1. Neue Tabelle erstellen

```sql
CREATE TABLE appointment_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NOT NULL,
    service_provider_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('accepted', 'rejected', 'rejected_with_suggestion')),
    message TEXT,
    suggested_date DATETIME,
    responded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
    FOREIGN KEY (service_provider_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(appointment_id, service_provider_id)
);

CREATE INDEX idx_appointment_responses_appointment ON appointment_responses(appointment_id);
CREATE INDEX idx_appointment_responses_provider ON appointment_responses(service_provider_id);
```

### 2. Backend API anpassen

```python
# app/models/appointment_response.py
class AppointmentResponse(Base):
    __tablename__ = "appointment_responses"
    
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    service_provider_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False)
    message = Column(Text)
    suggested_date = Column(DateTime)
    responded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    appointment = relationship("Appointment", back_populates="responses")
    service_provider = relationship("User")
```

### 3. API Endpoints

```python
# GET /api/v1/appointments/{appointment_id}/responses
# Alle Antworten für einen Termin

# POST /api/v1/appointments/{appointment_id}/respond
# Antwort erstellen/aktualisieren

# GET /api/v1/appointments/my-responses
# Alle eigenen Antworten
```

### 4. Frontend Integration

```typescript
interface AppointmentResponse {
  id: number;
  appointment_id: number;
  service_provider_id: number;
  service_provider?: {
    id: number;
    name: string;
    company_name?: string;
  };
  status: 'accepted' | 'rejected' | 'rejected_with_suggestion';
  message?: string;
  suggested_date?: string;
  responded_at: string;
}

interface Appointment {
  id: number;
  // ... andere Felder
  responses: AppointmentResponse[]; // Direkt als Array, kein JSON-String!
}
```

## Vorteile

1. **Keine JSON-Parsing-Probleme mehr**
2. **Bessere Performance** durch Indizes
3. **Einfache Queries** (z.B. "Alle akzeptierten Termine")
4. **Transaktionale Integrität**
5. **Einfache Erweiterbarkeit**

## Migration

1. Neue Tabelle erstellen
2. Bestehende JSON-Daten migrieren
3. Backend-Endpoints anpassen
4. Frontend auf neue Struktur umstellen
5. Alte `responses` Spalte entfernen 
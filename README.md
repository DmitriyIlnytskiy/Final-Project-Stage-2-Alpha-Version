# Vehicle Fleet & Service Hub

Full-stack vehicle service & workshop management platform built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, **JWT Authentication**, and a role-based **HTML/JS frontend**.

## Roles & Capabilities
- **Client (`client`)**: Register vehicles (with VIN validation), submit work orders, track repair status and itemized total cost.
- **Administrator (`admin`)**: View all work orders, assign mechanics (`In Progress`), manage service categories, catalog services, and parts inventory.
- **Mechanic (`mechanic`)**: View assigned work orders, log performed services, deduct parts from warehouse stock (auto-updating order totals), and mark orders `Completed`.

## Local Setup & Run Instructions
1. **Create PostgreSQL Database:** Create a database named `vehicle_service_db` in PostgreSQL (and verify connection string in `database.py`).
2. **Create Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
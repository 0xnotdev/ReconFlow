from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.services.pdf_service import generate_report_pdf, render_report_template
from jose import JWTError, jwt
from app.config import settings

router = APIRouter(prefix='/reports', tags=['reports'])

@router.get('/download')
def download_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.owner_id == current_user.id).first()
    pdf_bytes = generate_report_pdf(org, db)
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=reconflow-report.pdf'}
    )

@router.get('/view', response_class=HTMLResponse)
def view_report(
    token: str,
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise HTTPException(status_code=401, detail='Invalid token')
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail='User not found')

    org = db.query(Organization).filter(Organization.owner_id == user.id).first()
    if not org:
        raise HTTPException(status_code=404, detail='Organization not found')

    html_content = render_report_template(org, db)
    
    # Auto-trigger browser print dialog when the page loads
    print_script = """
    <script>
        window.onload = function() {
            window.print();
        }
    </script>
    """
    if "</body>" in html_content:
        html_content = html_content.replace("</body>", f"{print_script}</body>")
    else:
        html_content += print_script

    return HTMLResponse(content=html_content)

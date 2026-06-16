import httpx
import json
from app.models.discrepancy import Discrepancy
from app.config import settings

def build_action_prompt(d: Discrepancy) -> str:
    return f'''You are a financial revenue audit assistant for a bookkeeping agency.
Analyze the following accounting discrepancy and provide an action-first response.

Issue Type: {d.issue_type.value.replace('_', ' ').title()}
Amount: ${d.amount:.2f}
Customer: {d.customer_name or 'Unknown'}
Date: {d.date.strftime('%B %d, %Y') if d.date else 'Unknown'}
System Detected Cause: {d.suggested_cause}

Output ONLY valid JSON matching this schema exactly:
{{
  "what_happened": "Short factual description of the issue (1 sentence).",
  "why_it_matters": "Business impact, e.g. 'Financial reporting may be overstated by $X' (1 sentence).",
  "recommended_action": "Specific action the bookkeeper must take in QuickBooks/Stripe (1 sentence)."
}}'''

async def generate_action_recommendation(d: Discrepancy) -> bool:
    '''Generate actionable outputs for a discrepancy using OpenRouter free model'''
    if d.recommended_action:  # Already generated
        return True
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "ReconFlow"
        }
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [
                {"role": "user", "content": build_action_prompt(d)}
            ]
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            res_data = response.json()
            content = res_data['choices'][0]['message']['content'].strip()

        # Basic JSON extraction if markdown wrapped
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
            
        data = json.loads(content)
        
        d.what_happened = data.get('what_happened', d.suggested_cause)
        d.why_it_matters = data.get('why_it_matters', f"Revenue impact of ${d.amount:.2f}")
        d.recommended_action = data.get('recommended_action', "Investigate and resolve discrepancy.")
        d.ai_explanation = f"{d.what_happened} {d.why_it_matters} {d.recommended_action}"
        return True
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        # Fall back to rule-based explanation
        d.what_happened = d.suggested_cause
        d.why_it_matters = f"Possible revenue at risk: ${d.amount:.2f}"
        d.recommended_action = "Investigate in accounting system."
        return False

async def generate_explanation(d: Discrepancy) -> str:
    '''Generate and return the explanation string for a discrepancy'''
    await generate_action_recommendation(d)
    return d.ai_explanation or d.suggested_cause

async def batch_generate_explanations(discrepancies: list, db) -> None:
    '''Generate explanations for all open discrepancies without one'''
    for d in discrepancies:
        if not d.recommended_action:
            await generate_action_recommendation(d)
    db.commit()

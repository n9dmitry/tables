from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Функция для загрузки данных из JSON файла
def load_settings():
    with open('settings.json', 'r', encoding='utf-8') as f:
        return json.load(f)


# Функция для сохранения данных в JSON файл
def save_settings(data):
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class MaterialUpdate(BaseModel):
    name: str
    price_per_sqm: float
    width: float
    length: float
    roll_cost: float
    note: str

class AccessoryUpdate(BaseModel):
    name: str
    price_per_unit: float
    note: str

class PaintUpdate(BaseModel):
    liter_cost: float
    consumption_per_sqm: float
    printing_cost_per_sqm: float


@router.get("/settings", response_class=HTMLResponse)
async def read_settings(request: Request):
    settings = load_settings()
    return templates.TemplateResponse("settings.html", {"request": request, **settings})


@router.get("/settings/edit_material/{material_name}", response_class=HTMLResponse)
async def edit_material(request: Request, material_name: str):
    settings = load_settings()
    material = next((mat for mat in settings['materials'] if mat['name'] == material_name), None)
    if material is None:
        raise HTTPException(status_code=404, detail="Материал не найден")
    return templates.TemplateResponse("edit_material.html", {"request": request, "material": material})


@router.post("/settings/update_material/{material_name}", response_class=RedirectResponse)
async def update_material(
        material_name: str,
        name: str = Form(...),
        price_per_sqm: float = Form(...),
        width: float = Form(...),
        length: float = Form(...),
        roll_cost: float = Form(...),
        note: str = Form(...)
):
    settings = load_settings()
    for mat in settings['materials']:
        if mat['name'] == material_name:
            mat.update({
                "name": name,
                "price_per_sqm": price_per_sqm,
                "width": width,
                "length": length,
                "roll_cost": roll_cost,
                "note": note
            })
            save_settings(settings)
            return RedirectResponse(url="/settings", status_code=303)
    raise HTTPException(status_code=404, detail="Материал не найден")


@router.post("/settings/update_accessory/{accessory_name}", response_class=RedirectResponse)
async def update_accessory(
        accessory_name: str,
        name: str = Form(...),
        price_per_unit: float = Form(...),
        note: str = Form(...)
):
    settings = load_settings()
    for accessory in settings['accessories']:
        if accessory['name'] == accessory_name:
            accessory.update({
                "name": name,
                "price_per_unit": price_per_unit,
                "note": note
            })
            save_settings(settings)
            return RedirectResponse(url="/settings", status_code=303)
    raise HTTPException(status_code=404, detail="Аксессуар не найден")


@router.post("/settings/update_paint", response_class=RedirectResponse)
async def update_paint(
        liter_cost: float = Form(...),
        consumption_per_sqm: float = Form(...),
        printing_cost_per_sqm: float = Form(...)
):
    settings = load_settings()
    settings['paint'] = {
        "liter_cost": liter_cost,
        "consumption_per_sqm": consumption_per_sqm,
        "printing_cost_per_sqm": printing_cost_per_sqm
    }
    save_settings(settings)
    return RedirectResponse(url="/settings", status_code=303)


@router.post("/settings/update_rates", response_class=RedirectResponse)
async def update_rates(
        printer_rate_per_sqm: float = Form(...),
        eyelet_rate: float = Form(...),
        cutter_rate_per_sqm: float = Form(...),
        welder_rate: float = Form(...)
):
    settings = load_settings()
    settings['rates'] = {
        "printer_rate_per_sqm": printer_rate_per_sqm,
        "eyelet_rate": eyelet_rate,
        "cutter_rate_per_sqm": cutter_rate_per_sqm,
        "welder_rate": welder_rate
    }
    save_settings(settings)
    return RedirectResponse(url="/settings", status_code=303)


@router.get("/settings/edit_performers", response_class=HTMLResponse)
async def edit_performers(request: Request):
    settings = load_settings()
    return templates.TemplateResponse("edit_performers.html", {"request": request, "performers": settings.get('performers', [])})


@router.post("/settings/update_performers", response_class=RedirectResponse)
async def update_performers(
        performers: list[str] = Form(...),
):
    settings = load_settings()
    settings['performers'] = performers
    save_settings(settings)
    return RedirectResponse(url="/settings", status_code=303)


@router.get("/settings/edit_options", response_class=HTMLResponse)
async def edit_options(request: Request):
    settings = load_settings()
    return templates.TemplateResponse("edit_options.html", {"request": request, "options": settings.get('options', {})})


@router.post("/settings/update_options", response_class=RedirectResponse)
async def update_options(
        additional_option_available: bool = Form(...),
):
    settings = load_settings()
    settings['options']['additional_option'] = {'available': additional_option_available}
    save_settings(settings)
    return RedirectResponse(url="/settings", status_code=303)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de tareas del proyecto - Para usar cuando el servidor esté apagado
Guarda todo en tasks.json para persistencia
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Forzar UTF-8
sys.stdout.reconfigure(encoding='utf-8')

TASKS_FILE = Path(__file__).parent / "tasks.json"

def load_tasks():
    if TASKS_FILE.exists():
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"planes": [], "backlog": [], "registro": []}

def save_tasks(data):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_log(data, accion, descripcion, usuario="Sistema"):
    data["registro"].append({
        "timestamp": datetime.now().isoformat(),
        "accion": accion,
        "descripcion": descripcion,
        "usuario": usuario
    })

def cmd_status():
    data = load_tasks()
    print("\n" + "="*60)
    print("📋 ESTADO DEL PROYECTO")
    print("="*60)
    
    for plan in data["planes"]:
        print(f"\n📁 Plan: {plan['nombre']}")
        print(f"   Estado: {plan['estado']}")
        
        for task in plan["tareas"]:
            emoji = {"pendiente": "⏳", "en_proceso": "🔄", "completada": "✅"}.get(task["estado"], "❓")
            progreso = f" ({task.get('progreso', 0)}%)" if "progreso" in task else ""
            print(f"   {emoji} {task['titulo']}{progreso}")
    
    print(f"\n📥 Backlog: {len(data['backlog'])} tareas pendientes de aprobación")
    print(f"📝 Registro: {len(data['registro'])} entradas")
    print("="*60 + "\n")

def cmd_backlog():
    data = load_tasks()
    print("\n📥 BACKLOG (tareas propuestas):")
    for i, item in enumerate(data["backlog"], 1):
        print(f"  {i}. [{item['prioridad'].upper()}] {item['titulo']}")
        print(f"     {item['descripcion']}\n")

def cmd_log():
    data = load_tasks()
    print("\n📝 REGISTRO DE ACTIVIDAD:")
    for entry in data["registro"][-10:]:
        print(f"  {entry['timestamp'][:19]} | {entry['accion']} | {entry['descripcion']}")

def cmd_advance(task_id, progreso, notas=""):
    data = load_tasks()
    for plan in data["planes"]:
        for task in plan["tareas"]:
            if task["id"] == task_id:
                task["progreso"] = progreso
                if progreso >= 100:
                    task["estado"] = "completada"
                    task["fecha_completado"] = datetime.now().strftime("%Y-%m-%d")
                else:
                    task["estado"] = "en_proceso"
                if notas:
                    task["notas"] = notas
                add_log(data, "progreso", f"Tarea {task_id}: {progreso}% - {notas}")
                save_tasks(data)
                print(f"✅ Tarea {task_id} actualizada a {progreso}%")
                return
    print(f"❌ Tarea {task_id} no encontrada")

def cmd_complete(task_id, notas=""):
    data = load_tasks()
    for plan in data["planes"]:
        for task in plan["tareas"]:
            if task["id"] == task_id:
                task["estado"] = "completada"
                task["progreso"] = 100
                task["fecha_completado"] = datetime.now().strftime("%Y-%m-%d")
                if notas:
                    task["notas"] = notas
                add_log(data, "task_completada", f"Tarea {task_id} completada: {notas}")
                save_tasks(data)
                print(f"✅ Tarea {task_id} marcada como completada")
                return
    print(f"❌ Tarea {task_id} no encontrada")

def cmd_add_backlog(titulo, descripcion, prioridad="media"):
    data = load_tasks()
    new_id = f"backlog-{len(data['backlog'])+1:03d}"
    data["backlog"].append({
        "id": new_id,
        "titulo": titulo,
        "descripcion": descripcion,
        "prioridad": prioridad,
        "fecha_propuesto": datetime.now().strftime("%Y-%m-%d")
    })
    add_log(data, "backlog_add", f"Nueva tarea en backlog: {titulo}")
    save_tasks(data)
    print(f"✅ Añadido al backlog: {titulo}")

def cmd_approve(backlog_id, plan_id="plan-001"):
    data = load_tasks()
    for item in data["backlog"]:
        if item["id"] == backlog_id:
            # Add to plan
            for plan in data["planes"]:
                if plan["id"] == plan_id:
                    task_id = f"task-{len(plan['tareas'])+1:03d}"
                    plan["tareas"].append({
                        "id": task_id,
                        "titulo": item["titulo"],
                        "descripcion": item["descripcion"],
                        "estado": "pendiente",
                        "asignado": None,
                        "notas": "Aprobado desde backlog"
                    })
                    # Remove from backlog
                    data["backlog"].remove(item)
                    add_log(data, "backlog_approve", f"Tarea aprobada: {item['titulo']}")
                    save_tasks(data)
                    print(f"✅ Tarea '{item['titulo']}' movida al plan")
                    return
    print(f"❌ No se encontró la tarea {backlog_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_status()
    else:
        cmd = sys.argv[1]
        if cmd == "status":
            cmd_status()
        elif cmd == "backlog":
            cmd_backlog()
        elif cmd == "log":
            cmd_log()
        elif cmd == "advance" and len(sys.argv) >= 4:
            cmd_advance(sys.argv[2], int(sys.argv[3]), " ".join(sys.argv[4:]))
        elif cmd == "complete" and len(sys.argv) >= 3:
            cmd_complete(sys.argv[2], " ".join(sys.argv[3:]))
        elif cmd == "add" and len(sys.argv) >= 4:
            cmd_add_backlog(sys.argv[2], sys.argv[3])
        elif cmd == "approve" and len(sys.argv) >= 3:
            cmd_approve(sys.argv[2])
        else:
            print("Usage:")
            print("  python tasks.py status           # Ver estado")
            print("  python tasks.py backlog         # Ver backlog")
            print("  python tasks.py log             # Ver registro")
            print("  python tasks.py advance <id> <%> [notas]")
            print("  python tasks.py complete <id> [notas]")
            print("  python tasks.py add <titulo> <desc>")
            print("  python tasks.py approve <backlog-id>")

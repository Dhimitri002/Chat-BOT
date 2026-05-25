#!/usr/bin/env python3
"""
🌸 Flora Platform — Script de Execução Rápida

Uso:
    python run.py backend    # Inicia o backend FastAPI
    python run.py admin      # Inicia o app Admin (KivyMD)
    python run.py client     # Inicia o app Cliente (KivyMD)
    python run.py test       # Executa os testes
    python run.py setup      # Configura o ambiente inicial
    python run.py all        # Inicia backend + apps
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def check_env():
    """Verifica se .env existe."""
    if not Path(".env").exists():
        print("⚠️  Arquivo .env não encontrado!")
        print("   Copie .env.example para .env e configure:")
        print("   cp .env.example .env")
        return False
    return True


def setup():
    """Configura o ambiente inicial."""
    print("🌸 Configurando Flora Platform...")

    # Criar .env se não existir
    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ .env criado a partir de .env.example")
            print("   ⚠️  Edite .env com suas configurações!")
        else:
            print("❌ .env.example não encontrado!")
            return False

    # Criar diretórios necessários
    dirs = ["logs", "whatsapp_sessions", "uploads", "backups"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    print(f"✅ Diretórios criados: {', '.join(dirs)}")

    # Instalar dependências
    print("📦 Instalando dependências...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=True,
    )
    if result.returncode == 0:
        print("✅ Dependências instaladas!")
    else:
        print("⚠️  Algumas dependências falharam (normal em dev)")

    print("\n🌸 Flora Platform configurada!")
    print("   Próximos passos:")
    print("   1. Edite .env com suas configurações")
    print("   2. python run.py backend  (para iniciar o backend)")
    print("   3. python run.py admin    (para iniciar o app admin)")
    return True


def run_backend():
    """Inicia o backend FastAPI."""
    check_env()
    print("🌸 Iniciando Flora Backend...")
    print("   API: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    os.system(f"{sys.executable} -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")


def run_admin():
    """Inicia o app Admin."""
    check_env()
    print("🌸 Iniciando Flora Admin App...")
    os.system(f"{sys.executable} -m app_admin.main")


def run_client():
    """Inicia o app Cliente."""
    check_env()
    print("🌸 Iniciando Flora Client App...")
    os.system(f"{sys.executable} -m app_cliente.main")


def run_tests():
    """Executa os testes."""
    print("🧪 Executando testes...")
    os.system(f"{sys.executable} -m pytest tests/ -v --tb=short")


def run_all():
    """Inicia backend + apps em processos separados."""
    check_env()
    print("🌸 Iniciando Flora Platform (todos os serviços)...")

    processes = []

    # Backend
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    processes.append(("Backend", backend_proc))
    print("✅ Backend iniciado em http://localhost:8000")

    # Admin
    admin_proc = subprocess.Popen(
        [sys.executable, "-m", "app_admin.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    processes.append(("Admin", admin_proc))
    print("✅ Admin App iniciado")

    print("\n🌸 Todos os serviços iniciados!")
    print("   Pressione Ctrl+C para parar")

    try:
        for name, proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Parando serviços...")
        for name, proc in processes:
            proc.terminate()
            print(f"   {name} parado")
        print("🌸 Até logo!")


COMMANDS = {
    "setup": setup,
    "backend": run_backend,
    "admin": run_admin,
    "client": run_client,
    "test": run_tests,
    "all": run_all,
}


def main():
    parser = argparse.ArgumentParser(
        description="🌸 Flora Platform — Script de Execução",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Comandos disponíveis:
  setup    Configura o ambiente inicial
  backend  Inicia o backend FastAPI
  admin    Inicia o app Admin (KivyMD)
  client   Inicia o app Cliente (KivyMD)
  test     Executa os testes
  all      Inicia todos os serviços
        """,
    )
    parser.add_argument(
        "command",
        choices=COMMANDS.keys(),
        help="Comando a executar",
    )
    args = parser.parse_args()

    COMMANDS[args.command]()


if __name__ == "__main__":
    main()

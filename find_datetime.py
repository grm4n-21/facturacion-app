import os

def find_datetime_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                    # Buscar patrones de importación de datetime
                    if 'import datetime' in content or 'from datetime import' in content:
                        print(f"Archivo: {file_path}")
                        
                        # Extraer las líneas específicas para análisis
                        with open(file_path, 'r') as f2:
                            for i, line in enumerate(f2):
                                if 'datetime' in line and ('import' in line or 'from' in line):
                                    print(f"  Línea {i+1}: {line.strip()}")
                        print()

if __name__ == "__main__":
    # Ruta al directorio de tu proyecto
    project_directory = "."
    
    print("Analizando archivos Python para encontrar importaciones de datetime...\n")
    find_datetime_imports(project_directory)
    print("\nAnálisis completado.")
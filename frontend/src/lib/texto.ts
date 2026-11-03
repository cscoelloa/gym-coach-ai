export function nombreDeEjercicio(nombre: string): string {
  return nombre.replace(/(^|[\s(/-])(\p{L})/gu, (_, antes: string, letra: string) => {
    return antes + letra.toUpperCase();
  });
}

import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pygame
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from Tooltip import Tooltip

class Reproductor:
    # Iniciar pygame mixer
    pygame.mixer.init()

    pygame.init()

    # Variables globales
    archivo_actual = None
    estado_reproduccion = "detenido"
    posicion_actual = 0  # Para almacenar la posición actual de la canción en segundos
    volumen_actual = 0.5  # Control de volumen
    actualizando_manual = False  # Control para actualización manual de la barra

    pygame.mixer.music.set_endevent(pygame.USEREVENT)
    # Carpeta para cargar canciones
    directorio_musica = "Users\\sebas\\Downloads\\OkMusi"  # Actualiza la ruta de la carpeta de música

    def __init__(self):
        # Crear ventana principal
        self.ventana = tk.Tk()
        self.ventana.title("Reproductor de Música")
        self.ventana.geometry("800x800")
        self.ventana.config(bg="#1C2833")
        self.ventana.resizable(0,0)

        self.ventana_ayuda = None  # Atributo para rastrear la ventana de ayuda

        self.ventana.protocol("WM_DELETE_WINDOW", self.on_closing)
        

        # Crear un estilo personalizado para la barra de progreso
        self.estilo_barra = ttk.Style()
        self.estilo_barra.theme_use('clam')
        self.estilo_barra.configure(
            "custom.Horizontal.TProgressbar",
            troughcolor='#34495E',
            background='#2ECC71',
            darkcolor="#27AE60",
            lightcolor="#58D68D",
            bordercolor="#1ABC9C",
        )


        # Título del reproductor
        titulo = tk.Label(
            self.ventana, text="Reproductor MP3", font=("Arial", 24, "bold"), bg="#1C2833", fg="#ECF0F1"
        )
        titulo.pack(pady=(20, 2))

        # Contenedor principal para centralizar los elementos
        frame_principal = tk.Frame(self.ventana, bg="#1C2833")
        frame_principal.pack(padx=20, pady=10, fill="both", expand=True)

        # Crear un contenedor para la lista de canciones
        frame_lista = tk.Frame(frame_principal, bg="#1C2833")
        frame_lista.pack(pady=10)

        # Lista de canciones
        self.lista_canciones = tk.Listbox(
            frame_lista, width=40, height=15, selectmode=tk.SINGLE, bg="#FDFEFE", fg="#2C3E50", font=("Arial", 12), bd=2, relief="sunken"
        )
        self.lista_canciones.pack(padx=10, pady=10)

        self.actualizando_barra = True  # Controla si se actualiza la barra automáticamente

        # Botón para seleccionar carpeta de canciones
        btn_cargar = tk.Button(
            frame_principal, text="Seleccionar Carpeta", command=self.seleccionar_carpeta, width=20, bg="#5DADE2", fg="white", font=("Arial", 12, "bold"), bd=0, relief="flat"
        )
        btn_cargar.pack(pady=10)

        # Contenedor para controles y volumen
        frame_controles = tk.Frame(frame_principal, bg="#1C2833")
        frame_controles.pack(pady=10)

        # Controles de reproducción
        frame_botonera = tk.Frame(frame_controles, bg="#1C2833")
        frame_botonera.pack()

        # Cargar las imágenes de los botones de control
        self.imagen_reproducir = tk.PhotoImage(file="imagenes/reproducir.png").subsample(4, 4)
        self.imagen_pausar = tk.PhotoImage(file="imagenes/pausar.png").subsample(4, 4)
        self.imagen_detener = tk.PhotoImage(file="imagenes/detener.png").subsample(4, 4)
        self.imagen_retroceder = tk.PhotoImage(file="imagenes/anterior.png").subsample(4, 4)
        self.imagen_adelantar = tk.PhotoImage(file="imagenes/siquiente.png").subsample(4, 4)
        self.imagen_siguiente = tk.PhotoImage(file="imagenes/cancion_siquiente.png").subsample(4, 4)
        self.imagen_anterior = tk.PhotoImage(file="imagenes/cancion_anterior.png").subsample(4, 4)

        # Botones de control
        botones = [
            (self.imagen_anterior, lambda: self.cancion_anterior(None)),
            (self.imagen_retroceder, self.devolver_10_segundos),
            (self.imagen_reproducir, self.reproducir),
            (self.imagen_pausar, self.pausar),
            (self.imagen_detener, self.detener),
            (self.imagen_adelantar, self.avanzar_10_segundos),
            (self.imagen_siguiente, lambda: self.cancion_siguiente(None))
        ]

        for idx, (imagen, comando) in enumerate(botones):
            btn = tk.Button(
                frame_botonera, image=imagen, command=comando, bd=0, relief="flat", highlightthickness=0, bg="#1C2833"
            )
            btn.grid(row=0, column=idx, padx=5, pady=10)


            

        # Barra de progreso personalizada
        self.barra_progreso = ttk.Progressbar(
            frame_principal, style="custom.Horizontal.TProgressbar", orient="horizontal", length=600, mode="determinate"
        )
        self.barra_progreso.pack(pady=(10, 5))

        self.barra_progreso.bind("<Button-1>", self.adelantar_a_posicion)

        # Etiqueta para mostrar la duración y el tiempo transcurrido
        self.lbl_info = tk.Label(
            frame_principal, text="Duración: 00:00 / 00:00", bg="#1C2833", fg="#ECF0F1", font=("Arial", 12, "bold")
        )
        self.lbl_info.pack(pady=5)

        # Barra de volumen debajo de la duración
        self.volumen_slider = tk.Scale(
            frame_principal, from_=0, to=1, orient=tk.HORIZONTAL, resolution=0.01, label="Volumen", command=self.controlar_volumen, bg="#1C2833", fg="#ECF0F1", font=("Arial", 10, "bold"), bd=0
        )
        self.volumen_slider.set(0.5)
        self.volumen_slider.pack(pady=10)

       # Bind al evento de selección de canción
        self.lista_canciones.bind("<Double-1>", self.seleccionar_cancion)

        # Bind teclas para navegar entre canciones
        self.bind_teclas()

        btn_ayuda = tk.Button(
        frame_principal, 
        text="Ayuda", 
        command=self.mostrar_ayuda, 
        width=12,  # Un tamaño más pequeño para el botón
        bg="#5DADE2", 
        fg="white", 
        font=("Arial", 12, "bold"), 
        bd=0, 
        relief="flat"
    )
        btn_ayuda.place(relx=1.0, rely=0.05, anchor="ne", height=30, width=100)  # Colocamos el botón en la esquina superior derecha


        # Ejecutar la ventana principal
        self.ventana.mainloop()
    def mostrar_ayuda(self):
        """Mostrar una ventana emergente con los atajos de teclado"""
        if self.ventana_ayuda is None or not self.ventana_ayuda.winfo_exists():
            self.ventana_ayuda = tk.Toplevel(self.ventana)
            self.ventana_ayuda.title("Atajos de Teclado")
            self.ventana_ayuda.geometry("300x300")
            self.ventana_ayuda.config(bg="#1C2833")

            # Contenido de la ventana de ayuda
            texto_ayuda = """
            Atajos de Teclado:
            - Reproducir: Espacio
            - Pausar: p
            - Detener: s
            - Avanzar 10s: →
            - Retroceder 10s: ←
            - Canción Anterior: ↑
            - Canción Siguiente: ↓
            """
            etiqueta_ayuda = tk.Label(self.ventana_ayuda, text=texto_ayuda, bg="#1C2833", fg="#ECF0F1", font=("Arial", 12))

            etiqueta_ayuda.pack(pady=20)

            # Botón para cerrar la ventana de ayuda
            btn_cerrar = tk.Button(
                self.ventana_ayuda, text="Cerrar", command=self.cerrar_ventana_ayuda, width=15, bg="#E74C3C", fg="white", font=("Arial", 10, "bold"), bd=0, relief="flat"
            )
            btn_cerrar.pack(pady=10)

    def cerrar_ventana_ayuda(self):
        """Cerrar la ventana de ayuda."""
        if self.ventana_ayuda is not None:
            self.ventana_ayuda.destroy()  # Cerrar la ventana de ayuda
            self.ventana_ayuda = None  # Restablecer el atributo a None

    def bind_teclas(self):
        """Enlazar las teclas para los atajos de teclado"""
        self.ventana.bind("<Up>", self.cancion_anterior)
        self.ventana.bind("<Down>", self.cancion_siguiente)
        self.ventana.bind("<space>", self.reproducir)  # Atajo para reproducir
        self.ventana.bind("<p>", self.pausar)  # Atajo para pausar
        self.ventana.bind("<s>", self.detener)  # Atajo para detener
        self.ventana.bind("<Right>", self.avanzar_10_segundos)  # Atajo para avanzar 10 segundos
        self.ventana.bind("<Left>", self.devolver_10_segundos)  # Atajo para retroceder 10 segundos



    def cancion_anterior(self, event):
        """Seleccionar y reproducir la canción anterior en la lista"""
        seleccion = self.lista_canciones.curselection()
        if seleccion:
            indice_actual = seleccion[0]
            if indice_actual > 0:  # Evitar que baje del índice 0
                self.lista_canciones.selection_clear(0, tk.END)  # Limpiar selección
                self.lista_canciones.selection_set(indice_actual - 1)  # Seleccionar la anterior
                self.lista_canciones.activate(indice_actual - 1)  # Activar visualmente
                self.seleccionar_cancion(None)
            


    def cancion_siguiente(self, event):
        """Seleccionar y reproducir la siguiente canción en la lista."""
        seleccion = self.lista_canciones.curselection()
        if seleccion:
            indice_actual = seleccion[0]
            if indice_actual < self.lista_canciones.size() - 1:  # Evitar exceder el último índice
                self.lista_canciones.selection_clear(0, tk.END)  # Limpiar selección
                self.lista_canciones.selection_set(indice_actual + 1)  # Seleccionar la siguiente
                self.lista_canciones.activate(indice_actual + 1)  # Activar visualmente
                self.seleccionar_cancion(None)  # Reproducir la canción seleccionada



    def reproducir(self):
        """Reproducir o reanudar la canción seleccionada o detenida"""
        seleccion = self.lista_canciones.curselection()  # Obtener la canción seleccionada

        if seleccion:
            archivo_seleccionado = self.lista_canciones.get(seleccion[0])
            ruta_archivo = os.path.join(self.directorio_musica, archivo_seleccionado)

            if self.archivo_actual != ruta_archivo:  # Si la canción seleccionada es diferente a la actual
                self.archivo_actual = ruta_archivo
                pygame.mixer.music.load(self.archivo_actual)  # Cargar la canción seleccionada
                pygame.mixer.music.play()  # Reproducirla
                pygame.mixer.music.set_endevent(pygame.USEREVENT)  # Establecer el evento para fin de canción
                self.estado_reproduccion = "reproduciendo"
                self.posicion_actual = 0  # Reiniciar la posición al principio
                
                # Actualizar la barra de progreso inmediatamente
                self.barra_progreso['value'] = 0
                
                # Actualizar la duración total
                self.duracion_total = self.obtener_duracion()  # Asegúrate de que esta variable esté definida en la clase
                minutos_total = int(self.duracion_total // 60)
                segundos_total = int(self.duracion_total % 60)
                self.lbl_info.config(text=f"Duración: 00:00 / {minutos_total:02}:{segundos_total:02}")  # Mostrar duración total
                self.update_progress()  # Asegúrate de que la barra se actualice desde el principio
            elif self.estado_reproduccion == "pausado":  # Si la canción está pausada
                pygame.mixer.music.unpause()  # Reanudar la reproducción
                self.estado_reproduccion = "reproduciendo"  # Actualizar el estado
                self.update_progress()  # Actualizar la interfaz





    def pausar(self):
        """Pausar la música y guardar la posición actual"""
        if self.estado_reproduccion == "reproduciendo":
            pygame.mixer.music.pause()
            self.estado_reproduccion = "pausado"
            # Guardar la posición actual de la canción al momento de pausar
            self.posicion_actual = pygame.mixer.music.get_pos() / 1000  # Convertir de ms a segundos
            self.update_progress()  # Actualizar la interfaz con la nueva posición


    
    def detener(self):
        """Detener la canción y reiniciar la barra de progreso sin perder el archivo cargado"""
        if self.estado_reproduccion in ["reproduciendo", "pausado"]:
            pygame.mixer.music.stop()  # Detener la reproducción
            self.estado_reproduccion = "detenido"  # Marcar como detenido
            self.posicion_actual = 0  # Guardar la posición actual (en segundos)
            self.barra_progreso['value'] = 0  # Reiniciar la barra de progreso
            self.update_progress()  # Actualizar la interfaz
            
            # Actualizar la etiqueta de duración a 00:00/00:00
            self.lbl_info.config(text="Duración: 00:00 / 00:00")

    
    def avanzar_10_segundos(self, event=None):
        """Avanzar la canción 10 segundos y sincronizar la barra de progreso."""
        if self.archivo_actual and self.estado_reproduccion in ["reproduciendo", "pausado"]:
            duracion_total = self.obtener_duracion()
            nueva_posicion = min(self.posicion_actual + 10, duracion_total)  # Evitar exceder la duración total
            self.posicion_actual = nueva_posicion

            # Cambiar la posición de reproducción
            pygame.mixer.music.set_pos(self.posicion_actual)

            # Actualizar la barra de progreso y la etiqueta de duración inmediatamente
            self.update_progress_bar_and_label()

    def devolver_10_segundos(self, event=None):
        """Retroceder la canción 10 segundos y sincronizar la barra de progreso."""
        if self.archivo_actual and self.estado_reproduccion in ["reproduciendo", "pausado"]:
            nueva_posicion = max(self.posicion_actual - 10, 0)  # Evitar posiciones negativas
            self.posicion_actual = nueva_posicion

            # Cambiar la posición de reproducción
            pygame.mixer.music.set_pos(self.posicion_actual)

            # Actualizar la barra de progreso y la etiqueta de duración inmediatamente
            self.update_progress_bar_and_label()

    def update_progress_bar_and_label(self):
        """Actualizar la barra de progreso y la etiqueta de duración inmediatamente."""
        duracion_total = self.obtener_duracion()

        if duracion_total > 0:  # Evitar divisiones por 0
            # Calcular el progreso actual
            progress = (self.posicion_actual / duracion_total) * 100

            # Actualizar la barra de progreso
            self.barra_progreso['value'] = progress

            # Actualizar la etiqueta de duración
            minutos_actual = int(self.posicion_actual // 60)
            segundos_actual = int(self.posicion_actual % 60)
            minutos_total = int(duracion_total // 60)
            segundos_total = int(duracion_total % 60)
            self.lbl_info.config(
                text=f"Duración: {minutos_actual:02}:{segundos_actual:02}/{minutos_total:02}:{segundos_total:02}"
            )



    def seleccionar_carpeta(self):
        """Seleccionar carpeta con canciones y mostrar las canciones en la lista"""
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.directorio_musica = carpeta
            self.cargar_lista_canciones()

    def cargar_lista_canciones(self):
        """Cargar las canciones desde una carpeta específica"""
        self.lista_canciones.delete(0, tk.END)
        if os.path.isdir(self.directorio_musica):
            archivos = [f for f in os.listdir(self.directorio_musica) if f.endswith('.mp3')]
            for archivo in archivos:
                self.lista_canciones.insert(tk.END, archivo)

    def seleccionar_cancion(self, event):
        """Acción cuando se selecciona una canción"""
        seleccion = self.lista_canciones.curselection()
        if seleccion:
            archivo = self.lista_canciones.get(seleccion[0])
            ruta_archivo = os.path.join(self.directorio_musica, archivo)
            self.cargar_archivo(ruta_archivo)

    def cargar_archivo(self, archivo):
        """Cargar un archivo de música y reproducirlo"""
        self.archivo_actual = archivo
        pygame.mixer.music.load(archivo)
        pygame.mixer.music.play()
        self.estado_reproduccion = "reproduciendo"
        self.posicion_actual = 0
        self.update_progress()



    def reanudar_actualizacion_barra(self):
        """Reanudar la actualización automática de la barra de progreso."""
        self.actualizando_barra = True





    def controlar_volumen(self, val):
        """Controlar el volumen de la música"""
        volumen = float(val)
        pygame.mixer.music.set_volume(volumen)

    def obtener_duracion(self):
        """Obtener la duración total de la canción"""
        if self.archivo_actual:
            if self.archivo_actual.endswith(".mp3"):
                audio = MP3(self.archivo_actual)
                return audio.info.length
            elif self.archivo_actual.endswith(".wav"):
                audio = WAVE(self.archivo_actual)
                return audio.info.length
        return 0

    def adelantar_a_posicion(self, event):
        """Avanzar la canción a la posición en la que se hizo clic en la barra de progreso."""
        if self.archivo_actual and self.estado_reproduccion == "reproduciendo":  # Verificar si la música está en reproducción
            # Pausar la actualización automática
            self.actualizando_manual = True

            # Obtener la duración total de la canción
            duracion_total = self.obtener_duracion()

            if duracion_total > 0:  # Verificar que haya una duración válida
                # Calcular el porcentaje del clic en la barra
                porcentaje = event.x / self.barra_progreso.winfo_width()

                # Calcular la nueva posición en segundos
                nueva_posicion = porcentaje * duracion_total

                # Actualizar la posición de la canción
                self.posicion_actual = nueva_posicion

                # Usar set_pos para cambiar la posición directamente
                pygame.mixer.music.set_pos(self.posicion_actual)

                # Sincronizar la barra de progreso y la etiqueta inmediatamente
                self.barra_progreso['value'] = porcentaje * 100

                minutos_actual = int(self.posicion_actual // 60)
                segundos_actual = int(self.posicion_actual % 60)
                minutos_total = int(duracion_total // 60)
                segundos_total = int(duracion_total % 60)
                self.lbl_info.config(
                    text=f"Duración: {minutos_actual:02}:{segundos_actual:02}/{minutos_total:02}:{segundos_total:02}"
                )

            # Reanudar la actualización automática después de un breve momento
            self.ventana.after(1000, self.reanudar_actualizacion_barra)


    def update_progress(self):
        """Actualizar la barra de progreso y la etiqueta de tiempo."""
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:  # Verificar si la música ha terminado
                self.cancion_siguiente(None)  # Llamar a la función para reproducir la siguiente canción

        if self.archivo_actual and self.estado_reproduccion != "detenido":
            # Obtener el tiempo actual de reproducción
            if self.estado_reproduccion == "reproduciendo":
                current_time = pygame.mixer.music.get_pos() / 1000  # Obtener tiempo de reproducción en segundos
            else:
                current_time = self.posicion_actual  # Usar la posición almacaenada en pausa

            # Obtener la duración total de la canción
            duracion_total = self.obtener_duracion()

            if duracion_total > 0:  # Evitar divisiones por 0
                # Asegurarse de que el tiempo actual no supere la duración total
                current_time = max(0, min(current_time, duracion_total))  # Asegurarse de que no sea negativo

                # Calcular el progreso en porcentaje
                progress = (current_time / duracion_total) * 100

                # Actualizar la barra de progreso
                self.barra_progreso['value'] = progress

                # Actualizar la duración y el tiempo transcurrido en la etiqueta
                minutos_actual = int(current_time // 60)
                segundos_actual = int(current_time % 60)
                minutos_total = int(duracion_total // 60)
                segundos_total = int(duracion_total % 60)

                self.lbl_info.config(
                    text=f"Duración: {minutos_actual:02}:{segundos_actual:02}/{minutos_total:02}:{segundos_total:02}"
                )

                # Verificar si es la última canción de la lista
                seleccion = self.lista_canciones.curselection()
                if seleccion:
                    indice_actual = seleccion[0]
                    if indice_actual == self.lista_canciones.size() - 1:  # Si es la última canción
                        # Condicional para detener la canción si la duración actual y total son iguales
                        if current_time >= duracion_total:
                            self.detener()  # Detener la música
                            self.lbl_info.config(text="Duración: 00:00 / 00:00")  # Reiniciar la etiqueta de duración a 0
                            self.lista_canciones.selection_clear(0, tk.END)  # Limpiar la selección de la lista

        # Llamar a update_progress cada 500 ms, para que se actualice constantemente mientras se reproduce
        if self.estado_reproduccion == "reproduciendo":
            self.ventana.after(500, self.update_progress)

    def update_progress_continua(self):
            """Actualizar la barra de progreso continuamente mientras se reproduce la canción."""
            if self.estado_reproduccion == "reproduciendo":
                self.update_progress()  # Llamar a update_progress para actualizar la barra y la etiqueta de duración
                self.ventana.after(500, self.update_progress_continua)  # Continuar la actualización cada 500ms

    def on_closing(self):
        """Cerrar correctamente la ventana y liberar recursos de pygame."""
        pygame.mixer.music.stop()  # Detener cualquier música en reproducción
        pygame.quit()  # Cerrar pygame
        self.ventana.destroy()  # Cerrar la ventana






    def reanudar_actualizacion_barra(self):
        """Reanudar la actualización automática de la barra de progreso."""
        self.actualizando_manual = False  # Permitir que la barra se actualice automáticamente nuevamente

        

if __name__ == "__main__":
    Reproductor()
    

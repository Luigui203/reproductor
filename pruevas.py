import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pygame
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

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


    # Carpeta para cargar canciones
    directorio_musica = "Users\\sebas\\Downloads\\OkMusi"  # Actualiza la ruta de la carpeta de música

    def __init__(self):
        # Crear ventana principal
        self.ventana = tk.Tk()
        self.ventana.title("Reproductor de Música")
        self.ventana.geometry("800x800")
        self.ventana.config(bg="#1C2833")
        self.ventana.resizable(0,0)

        

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
        self.imagen_reproducir = tk.PhotoImage(file="images/reproducir.png").subsample(4, 4)
        self.imagen_pausar = tk.PhotoImage(file="images/pausar.png").subsample(4, 4)
        self.imagen_detener = tk.PhotoImage(file="images/detener.png").subsample(4, 4)
        self.imagen_retroceder = tk.PhotoImage(file="images/anterior.png").subsample(4, 4)
        self.imagen_adelantar = tk.PhotoImage(file="images/siquiente.png").subsample(4, 4)
        self.imagen_siguiente = tk.PhotoImage(file="images/cancion_siquiente.png").subsample(4, 4)
        self.imagen_anterior = tk.PhotoImage(file="images/cancion_anterior.png").subsample(4, 4)

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
        self.barra_progreso = ttk.Progressbar(frame_principal, style="custom.Horizontal.TProgressbar", orient="horizontal", length=600, mode="determinate")
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

        # Ejecutar la ventana principal
        self.ventana.mainloop()

    def formatear_tiempo(self, segundos):
        """Formatear el tiempo en formato MM:SS."""
        minutos = int(segundos) // 60
        segundos_restantes = int(segundos) % 60
        return f"{minutos:02}:{segundos_restantes:02}"


    def bind_teclas(self):
        """Enlazar las teclas arriba y abajo para cambiar de canción"""
        self.ventana.bind("<Up>", self.cancion_anterior)
        self.ventana.bind("<Down>", self.cancion_siguiente)

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
                self.update_progress()  # Asegúrate de que la barra se actualice desde el principio
                
                # Iniciar la actualización periódica de la barra de progreso
                self.actualizar_barra_progreso()

            elif self.estado_reproduccion == "pausado":  # Si está pausada, reanudar desde la posición actual
                pygame.mixer.music.unpause()  # Reanudar la canción
                self.estado_reproduccion = "reproduciendo"
                self.actualizar_barra_progreso()  # Reactivar la barra de progreso
            elif self.estado_reproduccion == "detenido":  # Si está detenida, reproducir desde la última posición guardada
                pygame.mixer.music.load(self.archivo_actual)  # Cargar la canción detenida
                pygame.mixer.music.play(start=self.posicion_actual)  # Reproducir desde la posición guardada
                self.estado_reproduccion = "reproduciendo"
                self.actualizar_barra_progreso()  # Actualizar la barra de progreso inmediatamente

    def actualizar_barra_progreso(self):
        """Actualizar la barra de progreso en intervalos regulares mientras la canción se reproduce"""
        if self.estado_reproduccion == "reproduciendo":
            # Actualizar la barra de progreso
            self.update_progress()

            # Reprogramar la actualización de la barra después de 500 ms
            self.ventana.after(500, self.actualizar_barra_progreso)

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
        if self.estado_reproduccion == "reproduciendo" or self.estado_reproduccion == "pausado":
            pygame.mixer.music.stop()  # Detener la reproducción
            self.estado_reproduccion = "detenido"  # Marcar como detenido
            self.posicion_actual = 0  # Guardar la posición actual (en segundos)
            self.barra_progreso['value'] = 0  # Reiniciar la barra de progreso
            self.update_progress()  # Actualizar la interfaz
            
            # Actualizar la etiqueta de duración a 00:00/00:00
            self.lbl_info.config(text="Duración: 00:00/00:00")

    
    def avanzar_10_segundos(self):
        """Avanzar la canción 10 segundos y sincronizar la barra de progreso."""
        if self.archivo_actual and self.estado_reproduccion in ["reproduciendo", "pausado"]:
            duracion_total = self.obtener_duracion()
            nueva_posicion = min(self.posicion_actual + 10, duracion_total)  # Evitar exceder la duración total
            self.posicion_actual = nueva_posicion

            if pygame.mixer.music.get_busy():  # Solo avanzar si la música está reproduciéndose
                pygame.mixer.music.set_pos(self.posicion_actual)
            else:
                # Si no está reproduciendo, reinicia la reproducción desde la nueva posición
                pygame.mixer.music.play(start=self.posicion_actual)

            # Actualizar la barra de progreso y la etiqueta de tiempo inmediatamente
            self.barra_progreso['value'] = (self.posicion_actual / duracion_total) * 100
            self.update_info_time(duracion_total)

    def devolver_10_segundos(self):
        """Retroceder la canción 10 segundos y sincronizar la barra de progreso."""
        if self.archivo_actual and self.estado_reproduccion in ["reproduciendo", "pausado"]:
            duracion_total = self.obtener_duracion()
            nueva_posicion = max(self.posicion_actual - 10, 0)  # Evitar que se vuelva negativa
            self.posicion_actual = nueva_posicion

            if pygame.mixer.music.get_busy():  # Solo retroceder si la música está reproduciéndose
                pygame.mixer.music.set_pos(self.posicion_actual)
            else:
                # Si no está reproduciendo, reinicia la reproducción desde la nueva posición
                pygame.mixer.music.play(start=self.posicion_actual)

            # Actualizar la barra de progreso y la etiqueta de tiempo inmediatamente
            self.barra_progreso['value'] = (self.posicion_actual / duracion_total) * 100
            self.update_info_time(duracion_total)


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
            self.actualizando_manual = False
            self.update_progress()  # Asegurar que la barra se siga actualizando correctamente



    def update_progress(self):
        """Actualizar la barra de progreso y la etiqueta con la duración actual."""
        if self.archivo_actual:
            duracion_total = self.obtener_duracion()
            if duracion_total > 0:  # Asegúrate de que la duración total no sea cero
                # Calcular los minutos y segundos de la duración total
                minutos_total = int(duracion_total // 60)
                segundos_total = int(duracion_total % 60)
                
                # Calcular los minutos y segundos de la posición actual
                minutos_actual = int(self.posicion_actual // 60)
                segundos_actual = int(self.posicion_actual % 60)

                # Formatear el tiempo para mostrarlo en el formato adecuado
                tiempo_formateado = f"{minutos_actual:02}:{segundos_actual:02}"
                tiempo_total_formateado = f"{minutos_total:02}:{segundos_total:02}"

                # Actualizar el label de tiempo
                self.lbl_info.config(text=f"Duración: {tiempo_formateado} / {tiempo_total_formateado}")

                # Actualizar la barra de progreso
                self.barra_progreso['value'] = (self.posicion_actual / duracion_total) * 100 #nción si la canción actual ha terminado

    def update_info_time(self, duracion_total):
        """Actualizar la etiqueta con la duración y el tiempo actual."""
        minutos_actual = int(self.posicion_actual // 60)
        segundos_actual = int(self.posicion_actual % 60)
        minutos_total = int(duracion_total // 60)
        segundos_total = int(duracion_total % 60)

        self.lbl_info.config(
            text=f"Duración: {minutos_actual:02}:{segundos_actual:02}/{minutos_total:02}:{segundos_total:02}"
        )

if __name__ == "__main__":
    Reproductor()
from typing import Iterable

import numpy as np

from .models import Config, TrackingFrameResult, TrackingPoint, TrackingSegment, TrackingResult, TrackingFrameMetadata, \
    TrackingPointStatus
from .tracking import interpolate_missing, gauss_fitting, generate_normal_line_bounds, multi_point_linear_interpolation, \
    points_linear_interpolation, profile_pos_to_point, bezier_fitting, read_line_from_img


def track_filament(frames: Iterable[np.ndarray], user_points: np.ndarray, config: Config) -> TrackingResult:
    results = []
    errors = []

    # Obtenemos los puntos iniciales del tracking interpolando linealmente los puntos del usuario
    prev_frame_points = multi_point_linear_interpolation(user_points, config.point_density)

    # Si no hay suficientes puntos para la tangente configurada, bajamos la cantidada de puntos
    max_tangent_length = min(config.max_tangent_length, len(prev_frame_points) - 1)

    for frame in frames:
        # Calculamos los limites que definen los segmentos de las rectas normales
        normal_lines_limits = generate_normal_line_bounds(prev_frame_points, max_tangent_length, config.normal_line_length)

        # A partir de los limites obtenemos la lista de pixeles que representan a los segmentos de las rectas normales
        # No es un ndarray porque no todas salen con la misma longitud (diagonales, etc)
        normal_lines = [points_linear_interpolation(start, end) for start, end in normal_lines_limits]

        # Obtenemos los perfiles de intensidad de la imagen de cada recta normal
        intensity_profiles = map(lambda nl, img=frame: read_line_from_img(img, nl), normal_lines)

        # Obtenemos la posicion del maximo punto del perfil de intensidad.
        # Puede retornar None en caso de que no se pueda fittear la curva de intensidad, o si el error es mayor al maximo permitido.
        points_profile_pos = list(map(lambda ip, img=frame: gauss_fitting(ip, img.max(), config.max_fitting_error), intensity_profiles))

        # A partir de las posiciones, obtenemos los puntos que representan.
        # En caso de que el error de la posicion fuese muy alto,
        #  o la posicion no estuviese dentro del perfil de intesidad, obtenemos None en vez del punto.
        raw_points_with_missing = [profile_pos_to_point(pos, nl) if pos else None for pos, nl in zip(points_profile_pos, normal_lines)]

        # Buscamos llenar los valores faltantes (None) mediante una interpolacion con los vecinos bien calculados.
        # En caso de que la interpolacion no pueda ser hecha, se descartan los valores.
        # Se informa la posicion de los valores interpolados o descartados.
        raw_points, interpolated_points, preserved_points = interpolate_missing(raw_points_with_missing, prev_frame_points, config.missing_inter_len)

        # Si fue seleccionado, suavizamos los puntos ajustando los mismos a una curva de bezier
        # Bezier puede fallar por cantidad maxima de puntos
        try:
            smoothed_points = bezier_fitting(raw_points) if config.bezier_smoothing else raw_points
        except ValueError as e:
            config.bezier_smoothing = False
            errors.append(str(e))
            smoothed_points = raw_points

        # Ya obtuvimos los puntos finales del frame! Los disponibilizamos como los puntos iniciales del proximo frame
        prev_frame_points = smoothed_points

        # Guardamos el resultado del frame
        results.append(TrackingFrameResult(
            TrackingPoint.from_arrays(prev_frame_points, {TrackingPointStatus.INTERPOLATED: interpolated_points, TrackingPointStatus.PRESERVED: preserved_points}),
            TrackingFrameMetadata(TrackingSegment.from_arrays(normal_lines_limits))
        ))

    return TrackingResult(results, errors)

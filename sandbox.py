import pandas as pd

frentes = pd.DataFrame({'frente': [1, 2, 3], 'rendimento': [105, 210, 1050]}).sort_values('rendimento')

blocos = pd.DataFrame({'bloco': [2387, 1536, 1739, 4575, 2430, 4342, 4509, 1242, 3520, 1126, 1651, 1249, 1658, 1447,
                                 4553, 2385, 3558, 1316, 1523, 2140, 4368, 4554, 4361, 1662, 4540, 4556, 2419, 2503,
                                 4555, 4547, 3518, 2508, 2447, 4507, 3591, 2434, 1736, 2322, 1123, 2609, 2440, 1166,
                                 4322, 2327, 3559, 4359, 1290, 3444, 1631, 2484, 1735, 2111, 1639, 3301, 2102, 1517,
                                 2216, 2404, 1526, 4552, 1187, 3412],
                       'area': [0.75, 1.35, 2.7, 3.36, 4.16, 4.29, 5.1, 5.75, 6.75, 6.79, 7.44, 8.71, 8.83, 10.34,
                                10.52, 10.67, 12.88, 14.8, 15.190000000000001, 16.11, 16.82, 17.63, 17.68, 18.16, 18.59,
                                19.83, 19.84, 19.990000000000002, 22.939999999999998, 23.03, 23.7, 28.909999999999997,
                                31.64, 35.08, 35.56, 35.62, 36.120000000000005, 39.9, 40.790000000000006, 41.87, 44.66,
                                44.88, 50.21, 53.63, 54.14, 57.349999999999994, 57.93, 61.58, 61.919999999999995,
                                63.620000000000005, 68.13, 75.98, 77.13999999999999, 78.27, 79.78, 80.27, 80.65,
                                83.22999999999999, 101.53999999999999, 148.82, 183.13,
                                235.22000000000003]}).sort_values('area')


def preenche_frentes(frentes, blocos):
    ultimo_bloco = 0
    total_blocos = len(blocos)
    blocos_da_frente = {}

    for _, frente_row in frentes.iterrows():
        frente = frente_row['frente']
        rendimento = frente_row['rendimento']
        acumulado = 0
        blocos_da_frente[frente] = []
        if ultimo_bloco + 1 < total_blocos:
            for i in range(ultimo_bloco, total_blocos):
                area = blocos.iloc[i]['area']
                ultimo_bloco = i
                if acumulado + area <= rendimento:
                    blocos_da_frente[frente].append(blocos.iloc[i]['bloco'])
                    acumulado += area
                else:
                    break

    return blocos_da_frente


resposta = preenche_frentes(frentes, blocos)

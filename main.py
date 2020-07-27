import os
import shutil
import tempfile
from datetime import datetime
from typing import List, Dict
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from pandas import DataFrame

from sirsaia import brasilio
from sirsaia import epiestim
from sirsaia import plotutils


def download(url, to_path):
    with open(to_path, 'wb') as f:
        f.write(requests.get(url, allow_redirects=True).content)


def get_global_dataset(dataset_csv, column_name):
    df_raw = pd.read_csv(
        'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'
        + dataset_csv
    )
    df = df_raw[df_raw['Country/Region'] == 'Brazil'].T
    df = df[4:].copy()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index().astype('i').diff().fillna(0)
    first_day = np.nonzero(df.values)[0][0]
    df = df.iloc[first_day:]
    df.columns = [column_name]
    return df


def get_brazil_dataset():
    brazil = get_global_dataset('time_series_covid19_confirmed_global.csv', 'local')
    brazil_dead = get_global_dataset('time_series_covid19_deaths_global.csv', 'deaths')
    return brazil.join(brazil_dead, how='outer').fillna(0)


def get_dataset_brasilio(fresh=False):
    casos = 'data/caso.csv.gz'
    if fresh:
        shutil.rmtree(casos, ignore_errors=True)
    if not os.path.exists(casos):
        download('https://data.brasil.io/dataset/covid19/caso.csv.gz', 'data/caso.csv.gz')
    return pd.read_csv('data/casos.csv.gz')


def get_dataset_tereos(xlsx=None):
    xlsx = xlsx or 'data/Dados R(t) Tereos.xlsx'
    return pd.read_excel(xlsx, 'Tereos')


def get_dataset_from_url(url, and_save_to_path=None):
    with tempfile.TemporaryDirectory() as temp:
        path = os.path.join(temp, url.split('/')[-1])
        download(url, path)
        df = pd.read_csv(path)
        if and_save_to_path:
            if os.path.exists(and_save_to_path):
                os.remove(and_save_to_path)
            shutil.move(path, and_save_to_path)
        return df


def plot_site(df):
    plt.subplot(2, 2, 1)
    plotutils.plot_it(df)
    left, right = plt.xlim()
    plotutils.despine()

    plt.subplot(2, 2, 2)
    plotutils.plot_it(df, deaths=True)
    plt.xlim(left=left, right=right)
    plotutils.despine()

    plt.subplot(2, 2, 4)
    plotutils.plot_weekdiff(df)
    plt.xlim(left=left, right=right)
    plotutils.despine()

    plt.subplot(2, 2, 3)
    cols = ['local']
    config = epiestim.make_config(mean_si=4.7, std_si=2.9)
    epiestim_result = epiestim.estimate_r(df[cols], config)
    plotutils.plot_result(epiestim_result, df)
    plt.xlim(left=left, right=right)

    plt.tight_layout(pad=2)
    return epiestim_result


def gera_graficos_para_as_cidades(dataset: DataFrame, state_cities: Dict[str, List[str]], include_state=False):
    for (state, state_cities) in state_cities.items():
        base_path = f'plots/{state}'
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        if include_state:
            state_df = brasilio.get_state(dataset, state)
            analyze_and_plot(state_df, base_path, state, None)

        for city in state_cities:
            # noinspection PyBroadException
            try:
                city_df = brasilio.get_city(dataset, state, city)
                analyze_and_plot(city_df, base_path, state, city)
            except Exception:
                print(f"Failed for {state}/{city}")


def analyze_and_plot(model_df, base_path, state, city):
    epiestim_result = plot_site(model_df)

    # save the image
    if city:
        image_path = os.path.join(base_path, f'{city}.png')
    elif state:
        image_path = os.path.join(base_path, f'{state}.png')
    else:
        raise Exception('state or city required')

    plt.savefig(image_path, dpi=72)
    plt.close()

    epiestim_result['t_start'] = model_df.index[(epiestim_result['t_start'] - 1).astype('i').values]
    epiestim_result['t_end'] = model_df.index[(epiestim_result['t_end'] - 1).astype('i').values]
    epiestim_result['country'] = 'Brazil'
    epiestim_result['state'] = state
    epiestim_result['city'] = city

    # TODO: save results
    # epiestim_result.to_csv(f'data/results_{state}_{city}.csv', mode='a', header=False)


def generate_zip():
    zipname = f"output/{datetime.now().strftime('%Y-%m-%d')}-covid-rt.zip"
    if os.path.exists(zipname):
        os.remove(zipname)
    with ZipFile(zipname, 'w') as zipObj:
        for folderName, subfolders, filenames in os.walk("plots/"):
            for filename in filenames:
                filepath = os.path.join(folderName, filename)
                zipObj.write(filepath, filepath)


def main():
    # garante que a pasta "./output/" exista
    if not os.path.exists('output'):
        os.makedirs('output')

    # limpa pasta de plots
    if os.path.exists("plots"):
        shutil.rmtree("plots")

    os.makedirs("plots")

    plotutils.init_matplotlib()
    plt.ion()
    plt.style.use('tableau-colorblind10')
    plt.rcParams['figure.figsize'] = (24, 16)

    brazil = get_brazil_dataset()
    epiestim_result = plot_site(brazil)
    plt.savefig('plots/Brasil.png', dpi=72)
    plt.close()

    # Imagens das cidades de interesse
    dataset_brasilio = get_dataset_from_url('https://data.brasil.io/dataset/covid19/caso.csv.gz')
    gera_graficos_para_as_cidades(
        dataset_brasilio,
        {
            'ES': ['Colatina'],
            'SP': ['São José do Rio Preto', 'Barretos', 'Olímpia', 'Severínia', 'Tanabi', 'Colina', 'Guaíra',
                   'Guapiaçu',
                   'Bebedouro', 'Pitangueiras', 'Mirassol', 'Monte Aprazível', 'Icém', 'Guaraci', 'Altair', 'São Paulo',
                   'Campinas'],
        },
        include_state=True)

    # Imagens da Tereos
    dataset_tereos = pd.read_excel('data/Dados R(t) Tereos.xlsx', 'Tereos')
    gera_graficos_para_as_cidades(dataset_tereos, {
        'SP': ['Tereos Andrade', 'Tereos São José', 'Tereos Mandu', 'Tereos Tanabi', 'Tereos Vertente',
               'Tereos Severínia', 'Tereos Cruz Alta']
    })

    generate_zip()


if __name__ == '__main__':
    main()

# Projet Spark : GraphX

## Introduction

Afin de travailler avec GraphX, nous avons souhaité utiliser avec une API dans laquelle il y aurait, selon nous, de nombreuses informations interconnectées. Nous pourrions alors faire apparapître des liens entre les différentes données, et ainsi faire du graph mining. Nous avons choisi d'utiliser les données de l'API IDF Mobilités, qui contient des données sur l'ensemble des transports en commun d'Île-de-France. 

### Structure de l'API et fonctionnalités
IDF Mobilités propose une API REST qui permet d'accéder à différentes données sur les transports en commun en Île-de-France à travers 14 endpoints ainsi que différents jeux de données qui peuvent être directement téléchargés dans différents formats (CSV, JSON, etc.). Les données disponibles incluent des informations sur les lignes de transport, les arrêts, les horaires, les incidents, et bien plus encore. L'API est bien documentée, ce qui facilite son utilisation pour récupérer les données nécessaires à notre projet ([voir ici](https://prim.iledefrance-mobilites.fr/fr/catalogue-data)).

### Accès aux données
Pour accéder aux données de l'API, il faut générer une clé d'API en créant un compte sur le site d'IDF Mobilités. Une fois la clé obtenue, nous pouvons faire des requêtes HTTP pour récupérer les données au format JSON. Nous avons utilisé `requests` en Python pour automatiser le processus de récupération des données et les stocker localement à l'aide de Kafka pour une utilisation ultérieure dans Spark et pour un archivage dans Garage.

## Description des commandes utilisées

## Résultats obtenus

## Conclusion


<style>
    h1 {text-align: center}
    body {text-align: justify}
</style>
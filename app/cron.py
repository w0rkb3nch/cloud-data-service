import os
import pathlib
import shutil
import yaml
from collection import Collection
from github import Github
from git import Repo
from huey import crontab, RedisHuey

huey = RedisHuey("cloud-data", host="redis")
collection = Collection()

REPO_FOLDER = "repositories"
TEMP_REPO_FOLDER = "temp_repositories"

pathlib.Path(REPO_FOLDER).mkdir(parents=True, exist_ok=True)

github_client = Github(os.environ.get("GITHUB_TOKEN"))


def get_data_from_software(base_directory, software, provider, softwares):
    desc_yml_path = os.path.join(base_directory, "desc.yml")
    if os.path.isfile(desc_yml_path):
        if software not in softwares:
            softwares[software] = {}
            softwares[software]["providers"] = {}
        if provider not in softwares[software]["providers"]:
            softwares[software]["providers"][provider] = {}
        with open(desc_yml_path, "r") as stream:
            try:
                yaml_data = yaml.safe_load(stream)
                softwares[software]["providers"][provider] = yaml_data[
                    "deployment_option"
                ]
            except yaml.YAMLError as exc:
                print(exc)


@huey.periodic_task(crontab(minute="*/1"))
def fetch_providers():
    softwares = {}
    if os.path.exists(TEMP_REPO_FOLDER):
        shutil.rmtree(TEMP_REPO_FOLDER)
    pathlib.Path(TEMP_REPO_FOLDER).mkdir(parents=True, exist_ok=True)
    for repo in github_client.search_repositories("org:w0rkb3nch"):
        if repo.name.startswith("cloud-"):
            print(f"🗃 Cloning {repo.clone_url}..", end="")
            software_direcotry = os.path.join(REPO_FOLDER, repo.name)
            temp_software_directory = os.path.join(TEMP_REPO_FOLDER, repo.name)
            Repo.clone_from(repo.clone_url, temp_software_directory)
            shutil.rmtree(os.path.join(temp_software_directory, ".git"))
            shutil.copytree(
                temp_software_directory, software_direcotry, dirs_exist_ok=True
            )
            print("Done!")
            print(f"📃 Fetching data from {repo.name}..", end="")
            for software in os.listdir(software_direcotry):
                get_data_from_software(
                    os.path.join(software_direcotry, software),
                    software,
                    repo.name,
                    softwares,
                )
            print("Done!")

    db_softwares = []
    for software_name, software_data in softwares.items():
        db_softwares.append({"name": software_name, **software_data})
    collection.insert_softwares(db_softwares)

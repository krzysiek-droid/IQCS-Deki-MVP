import datetime
import json
import time

import gfunctions
import gnrl_database_con
from gfunctions import log_exception

import pandas
import pandas as pd
from PyQt5 import QtGui
from PyQt5.QtWidgets import *

import shutil
import pathlib
import sys
import os

'''
Podcza instalacji aplikacji, należy ją połączyc z konkretną bazą danych i serwerem tzn. znać nazwę bazy i kody dostępu.
'''

with open(fr'D:\CondaPy - Projects\PyGUIs\DekiApp_pyqt5\db_settings.json', 'r') as readObject:
    database_settings = json.load(readObject)

mainConstructions_filepath = r'D:\dekiApp\Deki_ServerFiles\constructions_database\mainConstructions'
subConstructions_filepath = r'D:\dekiApp\Deki_ServerFiles\constructions_database\subConstructions'
srv_files_filepath = r'D:\dekiApp\Deki_ServerFiles\constructions_database'
srv_wps_files_path = r'D:\dekiApp\Deki_ServerFiles\wps_database'
weld_specification = ['id', 'belonging_construction_tag', 'belonging_construction_ID', 'wps_number', 'weld_id_prefix',
                      'weld_id_generated', 'weld_id_suffix', 'joint_type', 'weld_continuity_type', 'all_around',
                      'field_weld', 'upper_sizeType', 'upper_size', 'upper_weld_type', 'upper_weld_face',
                      'upper_weld_quant', 'upper_length', 'upper_weld_spacing', 'double_sided', 'sided_sizeType',
                      'sided_size', 'sided_weld_type', 'sided_weld_face', 'sided_weld_quant', 'sided_length',
                      'sided_weld_spacing', 'tail_info', 'first_material', 'second_material', 'first_welded_part',
                      'second_welded_part', 'testing_methods']

with open(r'D:\CondaPy - Projects\PyGUIs\DekiApp_pyqt5\db_settings.json', 'r') as s:
    reader = s.read()
    welds_cols = json.loads(reader)['modelWelds_columns']


class Construction:
    def __init__(self):
        print(f"INITIALIZING {self}...", end='')
        self.db: gnrl_database_con.Database = QApplication.instance().database
        self.table_name = None
        self.picture = None
        self.picturePath = None  # Path
        self.info = {}  # Dict
        self.stpModelPath = None
        self.pdfDocsPath = None
        self.db_records = None
        self.company_name = database_settings['company']
        self.folderPath = None
        self.parentConstructionObject = None
        self.mainConstructionObject = None
        self.mainWindowInstance = QApplication.instance().inspectionPlannerWindow

    # returns number of rows in database table (self.table_name)
    def update_records_amount(self):
        if self.db.is_table(self.table_name):
            self.db_records = 0 if self.db.check_records_number(
                self.table_name) is None else self.db.check_records_number(
                self.table_name)
            return self.db_records
        else:
            print(f'Could not find table {self.table_name} in database.')
            self.db_records = 0
            return 0

    def check_files(self) -> dict:
        if type(self.stpModelPath) == str and type(self.pdfDocsPath) == str:
            status = {'CAD': os.path.isfile(self.stpModelPath),
                      'Docs': os.path.isfile(self.pdfDocsPath)}
            return status


class MainConstruction(Construction):
    def __init__(self):
        super(MainConstruction, self).__init__()
        self.modelWelds_df = None
        self.subConstructions_df = None
        self.subConstructions_tableName = None
        self.modelWelds_tableName = None
        self.table_name = f"{self.company_name}_main_constructions"
        self.update_records_amount()
        self.mainConstructionObject = self
        self.released = False
        self.notReleasedColor = f"rgb(255, 150, 0);"
        self.releasedColor = f" rgb(30, 210, 80);"
        print(f" Initialization succeeded.")

    def save_main_construction(self):
        try:
            if not self.db.is_table(self.table_name):
                self.db.create_table(self.table_name, list(self.info.keys()))
                print('db_objects [save_main_construction]: New database created...', end=' ')
                self.save_main_construction()
            else:
                print('db_objects [save_main_construction]: Database found, adding...', end=" ")
                self.folderPath = mainConstructions_filepath + fr'\{self.info["serial_number"]}'
                try:
                    pathlib.Path.mkdir(pathlib.Path(self.folderPath))
                    print(f'db_objects [save_main_construction]: Directory {self.info["serial_number"]} created. ', end=' ')
                except FileExistsError:
                    print(f'db_objects [save_main_construction]: Directory {self.info["serial_number"]} already exists. Trying to save...', end=' ')

                # Prepare the folder for subConstructions
                try:
                    subs_path = subConstructions_filepath + fr"{self.info['serial_number']}"
                    pathlib.Path.mkdir(pathlib.Path(subs_path))
                    print(f'Directory {subs_path} created. ', end=' ')
                except FileExistsError:
                    print(f'db_objects [save_main_construction]: Directory for subConstructions -{subs_path}- already exists. Trying to save...', end=' ')

                dst_stpModelPath = self.folderPath + fr'\{self.info["serial_number"]}_cad.stp'
                self.stpModelPath = shutil.copy2(self.stpModelPath, dst_stpModelPath)
                print(f'db_objects [save_main_construction]: STEP model copied and saved.-----', end=" ")
                dst_pdfDocsPath = self.folderPath + fr'\{self.info["serial_number"]}_docs.pdf'
                self.pdfDocsPath = shutil.copy2(self.pdfDocsPath, dst_pdfDocsPath)
                print(f'db_objects [save_main_construction]: Docs copied and saved.-----', end=" ")
                self.picturePath = self.folderPath + fr'\{self.info["serial_number"]}_picture.png'
                self.picture.save(self.picturePath, 'png')
                # TODO add file creation confirmation notification with pathlib.Path.exist()
                print(f'db_objects [save_main_construction]: CAD model picture saved.-----')
                self.db.insert(self.table_name, self.info)

            # Create the database for subConstructions and welds
            self.db.create_table(f"{self.info['serial_number']}_sub_constructions",
                                 database_settings['subConstructions_columns'])
            self.db.create_table(f"{self.info['serial_number']}_model_welds", database_settings['modelWelds_columns'])
            # self.db.create_table(f"{self.info['serial_number']}_welds")
            return 1
        except Exception as e:
            print(f"db_objects [save_main_construction]: MainConstruction Object save failure -> {e}")
            return 0

    def load_info(self, construct_id):
        try:
            print(f'Loading data for mainConstruction with ID: {construct_id}....',
                  end=" ")
            keys = self.db.get_columns_names(self.table_name)
            values = self.db.get_row(self.table_name, 'id', f'{str(construct_id)}')[0]
            self.info = {k: v for k, v in zip(keys, values)}
            self.folderPath = mainConstructions_filepath + fr'\{self.info["serial_number"]}'
            self.picturePath = pathlib.Path(self.folderPath + fr'\{self.info["serial_number"]}_picture.png')
            # checks if picture is available
            if not self.picturePath.exists():
                print(f"\nPicture not found at given location!")
                raise FileNotFoundError
            self.picture = QtGui.QPixmap()
            self.picture.load(str(self.picturePath))
            self.stpModelPath = self.folderPath + fr'\{self.info["serial_number"]}_cad.stp'
            self.pdfDocsPath = self.folderPath + fr'\{self.info["serial_number"]}_docs.pdf'
            if self.db.is_table(f"{self.info['serial_number']}_welds"):
                self.released = True
            self.modelWelds_tableName = f"{self.info['serial_number']}_modelWelds"
            self.subConstructions_tableName = f"{self.info['serial_number']}_sub_constructions"
            self.subConstructions_df = self.db.table_into_DF(f"{self.info['serial_number']}_sub_constructions")
            self.modelWelds_df = self.db.table_into_DF(f"{self.info['serial_number']}_modelWelds")
            print(f'Construction {self.info["name"]}-{self.info["serial_number"]} loaded.')
            return 1
        except Exception as e:
            print(f"Loading data for {self} failed err-> {e}")
            return 0

    def releaseConstruction(self, new_table_values: pd.DataFrame):
        try:
            realWelds_tableName = f"{self.info['serial_number']}_welds"
            self.db.create_table_2(realWelds_tableName, new_table_values.columns.tolist(), new_table_values)
            self.info['released_by'] = 'admin'
            self.info['released_time'] = datetime.datetime.now()
            self.db.replace_row(self.table_name, self.info, int(self.info['id']))
        except Exception as exc:
            print(gfunctions.log_exception(exc))
            return 0


class SubConstruction(Construction):
    def __init__(self, mainConstructionObject, parentConstructionObject=None):
        super(SubConstruction, self).__init__()
        self.info = {}

        if parentConstructionObject is None:
            self.parentConstructionObject = mainConstructionObject
        else:
            self.parentConstructionObject = parentConstructionObject

        self.mainConstructionObject = mainConstructionObject
        self.table_name = self.mainConstructionObject.info['serial_number'] + '_SubConstructions'

        if self.mainWindowInstance.cached_data['subConstructions_db'] is not None:
            self.db_content: pandas.DataFrame = self.mainWindowInstance.cached_data['subConstructions_db']
        else:
            print(f"\ndb_objects | SubConstruction __init__ | loading welds data from database {self.table_name}...",
                  end=' ')
            self.db_content: pandas.DataFrame = self.db.table_into_DF(self.table_name)
            print(f"Caching data...", end=' ')
            self.mainWindowInstance.cached_data.update({'subConstructions_db': self.db_content})
            print(f"Done.")

        self.info = dict.fromkeys(self.db_content.columns.tolist())

    def get_children(self) -> pd.DataFrame:
        try:
            if len(self.db_content) == self.db.check_records_number(self.table_name):
                belonging_constructions = self.db.get_subConstruction_branch(self.info['id'], df=self.db_content)
                return belonging_constructions
            else:
                self.db_content = self.db.table_into_DF(self.table_name)
                self.mainWindowInstance.cached_data.update({'subConstructions_db': self.db_content})
                return self.get_children()
        except Exception as exc:
            print(log_exception(exc))
            return pd.DataFrame()

    def get_belonging_welds(self) -> pd.DataFrame:
        try:
            welds_df = self.mainWindowInstance.cached_data['modelWelds_db']
            if welds_df is None:
                welds_df = self.db.table_into_DF(f"{self.mainConstructionObject.info['serial_number']}_modelWelds")
                self.mainWindowInstance.cached_data.update({'modelWelds_db': welds_df})
            b_welds_df = welds_df[welds_df['belonging_construction_ID'] == self.info['id']]
            return b_welds_df
        except Exception as exc:
            print(log_exception(exc))
            return pd.DataFrame()

    def save_subConstruction(self):
        try:
            self.folderPath = subConstructions_filepath + fr'\{self.mainConstructionObject.info["serial_number"]}'

            self.folderPath = self.folderPath + fr'\{self.info["serial_number"]}'
            try:
                pathlib.Path.mkdir(pathlib.Path(self.folderPath))
                print(f'Directory {self.folderPath} created. ')
            except FileExistsError:
                print(f'Directory {self.info["serial_number"]} already exists.')

            dst_stpModelPath = self.folderPath + fr'\{self.info["tag"]}_cad.stp'
            self.stpModelPath = shutil.copy2(self.stpModelPath, dst_stpModelPath)
            print(f'STEP model copied and saved.-----', end=" ")
            dst_pdfDocsPath = self.folderPath + fr'\{self.info["tag"]}_docs.pdf'
            self.pdfDocsPath = shutil.copy2(self.pdfDocsPath, dst_pdfDocsPath)
            print(f'Docs copied and saved.-----', end=" ")
            self.picturePath = self.folderPath + fr'\{self.info["tag"]}_picture.png'
            self.picture.save(self.picturePath, 'png')
            # TODO add file creation confirmation notification with pathlib.Path.exist()
            print(f'CAD model picture saved.-----', end=" ")
            self.db.insert(self.table_name, self.info)
            print(f"SubConstruction -> {self.info['name']} added to database -> {self.table_name}.")

            # Update the cached data
            self.db_content.append(self.info, ignore_index=True)
            return 1
        except Exception as e:
            print(f"SubConstruction {self} save failure err-> {e}")
            return 0

    def load_info(self, construct_id):
        try:
            keys = self.db.get_columns_names(self.table_name)
            values = self.db.get_row(self.table_name, 'id', f'{str(construct_id)}')[0]
            self.info = {k: v for k, v in zip(keys, values)}

            # Set filepath to subConstructions folder belonging to mainConstruction
            self.folderPath = subConstructions_filepath + fr'\{self.mainConstructionObject.info["serial_number"]}'
            # Add to filepath the tag of subconstruction
            self.folderPath = self.folderPath + fr'\{self.info["serial_number"]}'

            self.picturePath = pathlib.Path(self.folderPath + fr'\{self.info["tag"]}_picture.png')
            # checks if picture is available
            if not self.picturePath.exists():
                print(f"Picture not found at given location! -> {self.picturePath}")
                raise FileNotFoundError
            self.picture = QtGui.QPixmap()
            self.picture.load(str(self.picturePath))
            self.stpModelPath = self.folderPath + fr'\{self.info["tag"]}_cad.stp'
            self.pdfDocsPath = self.folderPath + fr'\{self.info["tag"]}_docs.pdf'
            return 1
        except Exception as e:
            print(f"Error during loading function of {self} --> {e}")
            return 0


class WeldObject:
    def __init__(self):
        self.mainWindowInstance = QApplication.instance().inspectionPlannerWindow
        self.mainConstructionObject = self.mainWindowInstance.cached_data['mainConstructionObject']
        if self.mainConstructionObject is not None:
            self.table_name = f"{self.mainConstructionObject.info['serial_number']}_modelWelds"
        else:
            print(f"Weld object -> {self} has no mainConstruction object, therefore needs to be closed")
            return
        self.db = QApplication.instance().database
        self.db_records = self.update_records_amount()
        self.wps_filepath = None
        if self.mainWindowInstance.cached_data['modelWelds_db'] is not None:
            self.db_content: pandas.DataFrame = self.mainWindowInstance.cached_data['modelWelds_db']
        else:
            print(f"\ndb_objects | WeldObject __init__ | loading welds data from database {self.table_name}...",
                  end=' ')
            self.db_content: pandas.DataFrame = self.db.table_into_DF(self.table_name)
            print(f"Caching data in mainWindowInstance...", end=' ')
            self.mainWindowInstance.cached_data.update({'modelWelds_db': self.db_content})
            print(f"done")

        self.info = dict.fromkeys(self.db_content.columns.tolist())
        self.sameWeldsAmount = None

    # returns number of rows in database table (self.table_name)
    def update_records_amount(self):
        if self.db.is_table(self.table_name):
            self.db_records = 0 if self.db.check_records_number(
                self.table_name) == 0 else self.db.check_records_number(
                self.table_name)
            return self.db_records
        else:
            print(f'Could not find table {self.table_name} in database. No records updated.')
            self.db_records = None
            return None

    def fast_load_singleWeld(self, weldID):
        values = self.db_content.iloc[weldID - 1].tolist()
        self.info = {k: v for k, v in zip(self.info.keys(), values)}
        if self.info["wps_number"] != 'missing':
            self.wps_filepath = srv_wps_files_path + fr'\{self.info["wps_number"]}.pdf'
        else:
            self.wps_filepath = "missing"
        self.info['testing_methods'] = self.info['testing_methods'].split(';')
        self.sameWeldsAmount = int(len(self.db_content.loc[self.db_content['same_as_weldID'] ==
                                                           self.info['weld_id_generated']])) + 1

    def save_weld(self, pathToWpsFile):
        if pathToWpsFile is not None:
            dst_wpsDocsPath = srv_wps_files_path + fr'\{self.info["wps_number"]}.pdf'
            self.wps_filepath = shutil.copy2(pathToWpsFile, dst_wpsDocsPath)
        else:
            self.info.update({'wps_number': 'missing'})

        try:
            self.update_records_amount()
            self.info.update({'id': int(self.db_records) + 1})
            print(f'Inserting new weld... {self.info}', end=" ")
            self.db.insert(self.table_name, self.info)
            print(f'Weld inserted with id: {self.info["id"]}')
            return 1
        except Exception as e:
            print(f"db_objects | Func(save_weld) failure | err-> {e}")
            return 0

    def replace_weld(self, pathToWpsFile, old_sameWelds: pd.DataFrame = None):
        dst_wpsDocsPath = srv_wps_files_path + fr'\{self.info["wps_number"]}.pdf'

        if old_sameWelds is None:
            sameWelds_df = self.db_content.loc[self.db_content['same_as_weldID'] == self.info['weld_id_generated']]
        else:
            # Old rows of the same welds must have been passed through constructor since the id of weld changes for
            # every next same weld row
            sameWelds_df = old_sameWelds

        try:
            if sameWelds_df.empty:
                self.db.replace_row(self.table_name, self.info)
                print(f'Weld replaced at id: {self.info["id"]}')

            else:
                self.db.replace_row(self.table_name, self.info)
                self.info['same_as_weldID'] = self.info['weld_id_generated']
                primary_id = self.info['weld_id_generated']
                i = 1
                for index, row in sameWelds_df.iterrows():
                    self.info['weld_id_generated'] = primary_id + f'#{i}'
                    self.db.replace_row(self.table_name, self.info, int(row['id']))
                    i += 1
                print(f'Welds replaced at ids: {sameWelds_df["id"].tolist()}')
        except Exception as e:
            print(f"Couldn't replace weld  err-> {e}")

        if pathToWpsFile is not None:
            self.wps_filepath = shutil.copy2(pathToWpsFile, dst_wpsDocsPath)

    def check_files(self):
        return os.path.isfile(self.wps_filepath)


def measureTime(obj, args: list):
    ts = time.time()
    rObj = obj(*args)
    tf = time.time()
    return rObj, tf - ts


if __name__ == "__main__":
    from Screens.mainWindow import DekiDesktopApp

    app = DekiDesktopApp(sys.argv)

    from Screens.inspectionPlannerWindow_SCRIPT import InspectionPlannerWindow

    ins = InspectionPlannerWindow()
    app.inspectionPlannerWindow = ins
    # ins.show()
    mC = MainConstruction()
    print(f'main construction initialized')
    mC.load_info(1)
    ins.cached_data['mainConstructionObject'] = mC

    try:
        sC = SubConstruction(mC)
        sC.load_info(2)
    except Exception as e:
        print(f"Exception {e}")

    try:
        sys.exit(app.exec_())
    except:
        print("Exiting the App")

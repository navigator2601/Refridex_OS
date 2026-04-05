# datavase/update_models_cond.py
import psycopg2
from datetime import datetime

# Припустимо, що DB_CONNECTION_STRING та conditioner_data імпортовані або визначені
# ЗВЕРНІТЬ УВАГУ: ЦІ ЗМІННІ МАЮТЬ БУТИ ВИЗНАЧЕНІ ПЕРЕД ЦІЄЮ ФУНКЦІЄЮ!
# Наприклад:
DB_CONNECTION_STRING = "postgresql://kondiki:avrora@localhost:5432/base_bot"
# conditioner_data = { ... } # Ваш словник з даними кондиціонерів

# Ваша функція get_id_from_db (з попередніх частин)
def get_id_from_db(cursor, table_name, id_column, value, **kwargs):
    conditions = []
    params = []

    query = f"SELECT {id_column} FROM conditioners.{table_name} WHERE "

    if table_name == "recommended_areas":
        conditions.append("area_sqm = %s")
        params.append(value)
    elif table_name == "unit_weights":
        conditions.append("net_kg = %s AND gross_kg = %s")
        params.append(kwargs["net_kg"])
        params.append(kwargs["gross_kg"])
    elif table_name == "unit_component_properties":
        conditions.append("length_mm = %s AND depth_mm = %s AND height_mm = %s AND component_type_id = %s")
        params.append(value) # length_mm
        params.append(kwargs["depth_mm"])
        params.append(kwargs["height_mm"])
        params.append(kwargs["component_type_id"])
        if kwargs.get("packed_length_mm") is not None:
            conditions.append("packed_length_mm = %s")
            params.append(kwargs["packed_length_mm"])
        if kwargs.get("packed_depth_mm") is not None:
            conditions.append("packed_depth_mm = %s")
            params.append(kwargs["packed_depth_mm"])
        if kwargs.get("packed_height_mm") is not None:
            conditions.append("packed_height_mm = %s")
            params.append(kwargs["packed_height_mm"])
    elif table_name == "brands":
        conditions.append("brand_name = %s")
        params.append(kwargs["brand_name"])
    elif table_name == "conditioner_types":
        conditions.append("type_name_ukr = %s")
        params.append(kwargs["type_name_ukr"])
    elif table_name == "conditioner_energy_efficiency":
        conditions.append("class_name = %s")
        params.append(kwargs["class_name"])
    elif table_name == "conditioner_model_names":
        conditions.append("model_name_ukr = %s")
        params.append(kwargs["model_name_ukr"])
    elif table_name == "internal_units" or table_name == "external_units" or table_name == "panels":
        conditions.append("unit_name = %s" if table_name in ["internal_units", "external_units"] else "model_name = %s")
        params.append(value)
    elif table_name == "compressor_manufacturers":
        conditions.append("manufacturer_name = %s")
        params.append(kwargs["manufacturer_name"])
    elif table_name == "compressor_types":
        conditions.append("type_name_ukr = %s")
        params.append(kwargs["type_name_ukr"])
    elif table_name == "refrigerant_types":
        conditions.append("type_name = %s")
        params.append(kwargs["type_name"])
    elif table_name == "warranty_periods":
        conditions.append("years = %s")
        params.append(kwargs["years"])
    elif table_name == "operation_modes":
        conditions.append("mode_name_ukr = %s")
        params.append(kwargs["mode_name_ukr"])
    elif table_name == "allowed_voltage_ranges":
        conditions.append("min_voltage = %s AND max_voltage = %s AND unit = %s")
        params.append(value)
        params.append(kwargs["max_voltage"])
        params.append(kwargs["unit"])
    elif table_name == "voltage_frequency_phases":
        conditions.append("voltage_range = %s AND phase = %s AND frequency_hz = %s")
        params.append(value)
        params.append(kwargs["phase"])
        params.append(kwargs["frequency_hz"])
    elif table_name == "temperature_setting_ranges":
        conditions.append("min_temp_celsius = %s AND max_temp_celsius = %s")
        params.append(value)
        params.append(kwargs["max_temp_celsius"])
    elif table_name == "indoor_operating_temp_ranges" or table_name == "outdoor_operating_temp_ranges":
        conditions.append("cooling_min_celsius = %s AND cooling_max_celsius = %s AND heating_min_celsius = %s AND heating_max_celsius = %s")
        params.append(value)
        params.append(kwargs["cooling_max_celsius"])
        params.append(kwargs["heating_min_celsius"])
        params.append(kwargs["heating_max_celsius"])
    elif table_name == "watt_specs":
        conditions.append("nominal_watt_value = %s AND min_watt_value = %s AND max_watt_value = %s AND operation_mode_id = %s")
        params.append(value)
        params.append(kwargs["min_watt_value"])
        params.append(kwargs["max_watt_value"])
        params.append(kwargs["operation_mode_id"])
    elif table_name == "btu_specs":
        conditions.append("nominal_btu_value = %s AND min_btu_value = %s AND max_btu_value = %s AND operation_mode_id = %s")
        params.append(value)
        params.append(kwargs["min_btu_value"])
        params.append(kwargs["max_btu_value"])
        params.append(kwargs["operation_mode_id"])
    elif table_name == "power_consumption_specs":
        conditions.append("nominal_consumption_watt = %s AND min_consumption_watt = %s AND max_consumption_watt = %s AND operation_mode_id = %s")
        params.append(value)
        params.append(kwargs["min_consumption_watt"])
        params.append(kwargs["max_consumption_watt"])
        params.append(kwargs["operation_mode_id"])
    elif table_name == "current_specs":
        conditions.append("nominal_current_amp = %s AND min_current_amp = %s AND max_current_amp = %s AND operation_mode_id = %s")
        params.append(value)
        params.append(kwargs["min_current_amp"])
        params.append(kwargs["max_current_amp"])
        params.append(kwargs["operation_mode_id"])
    elif table_name == "energy_efficiency_specs":
        if "seer" in kwargs and kwargs["seer"] is not None:
            conditions.append("seer = %s AND operation_mode_id = %s AND energy_efficiency_class_id = %s")
            params.append(kwargs["seer"])
            params.append(kwargs["operation_mode_id"])
            params.append(kwargs["energy_efficiency_class_id"])
        elif "scop" in kwargs and kwargs["scop"] is not None:
            conditions.append("scop = %s AND operation_mode_id = %s AND energy_efficiency_class_id = %s")
            params.append(kwargs["scop"])
            params.append(kwargs["operation_mode_id"])
            params.append(kwargs["energy_efficiency_class_id"])
        else:
            return None # Should not happen if data is valid
    elif table_name == "indoor_air_flow_specs":
        conditions.append("high_cmh = %s AND medium_cmh = %s AND low_cmh = %s")
        params.append(value)
        params.append(kwargs["medium_cmh"])
        params.append(kwargs["low_cmh"])
    elif table_name == "max_electrical_specs":
        conditions.append("max_power_consumption_watt = %s AND max_current_amp = %s")
        params.append(value)
        params.append(kwargs["max_current_amp"])
    elif table_name == "indoor_noise_levels":
        conditions.append("high_db = %s AND medium_db = %s AND low_db = %s")
        params.append(value)
        params.append(kwargs["medium_db"])
        params.append(kwargs["low_db"])
        if kwargs.get("sleep_db") is not None:
            conditions.append("sleep_db = %s")
            params.append(kwargs["sleep_db"])
    elif table_name == "outdoor_air_flow_specs":
        conditions.append("volume_cmh = %s")
        params.append(value)
    elif table_name == "outdoor_noise_levels":
        conditions.append("db_value = %s")
        params.append(value)
    elif table_name == "refrigerant_charges":
        conditions.append("weight_kg = %s AND oil_volume_ml = %s AND oil_type = %s")
        params.append(value)
        params.append(kwargs["oil_volume_ml"])
        params.append(kwargs["oil_type"])
    elif table_name == "refrigerant_pipe_specs":
        conditions.append("liquid_line_mm = %s AND liquid_line_inch = %s AND gas_line_mm = %s AND gas_line_inch = %s AND max_length_m = %s AND max_height_diff_m = %s")
        params.append(value) # liquid_line_mm
        params.append(kwargs["liquid_inch"])
        params.append(kwargs["gas_mm"])
        params.append(kwargs["gas_inch"])
        params.append(kwargs["max_length"])
        params.append(kwargs["max_height_diff"])
    elif table_name == "power_supply_locations":
        conditions.append("location_name_ukr = %s")
        params.append(kwargs["location_name_ukr"])
    elif table_name == "power_cables_specs":
        power_cable_mm2_val = str(kwargs["power_cable_mm2"]).replace('×', 'x') if kwargs.get("power_cable_mm2") is not None else None
        interconnect_cable_mm2_val = str(kwargs["interconnect_cable_mm2"]).replace('×', 'x') if kwargs.get("interconnect_cable_mm2") is not None else None
        conditions.append("power_cable_mm2 = %s AND interconnect_cable_mm2 = %s")
        params.append(power_cable_mm2_val)
        params.append(interconnect_cable_mm2_val)
    elif table_name == "component_types":
        conditions.append("type_name_ukr = %s")
        params.append(kwargs["type_name_ukr"])
    else:
        # Цей блок повинен бути для простих таблиць з одним параметром.
        # Забезпечуємо, що value не None, якщо це ключовий параметр пошуку.
        if value is not None:
            conditions.append(f"{id_column} = %s") # Це може бути проблемою, якщо id_column використовується як пошуковий параметр
            params.append(value)
        else:
            # Для таблиць, де value є None, але kwargs містить унікальний параметр (як model_name_ukr, brand_name, type_name_ukr)
            # Ми вже обробляємо їх окремо вище. Якщо це інша "проста" таблиця, то потрібно додати її сюди.
            raise ValueError(f"Value cannot be None for table {table_name} with id_column {id_column} without specific kwargs.")


    # Виконуємо запит на пошук
    full_query = query + " AND ".join(conditions)

    # Логування пошуку
    log_value = value if value is not None else (kwargs.get('model_name_ukr') or kwargs.get('brand_name') or kwargs.get('type_name_ukr') or kwargs.get('manufacturer_name') or kwargs.get('class_name') or kwargs.get('mode_name_ukr') or kwargs.get('type_name') or kwargs.get('years') or kwargs.get('location_name_ukr') or "None")
    print(f"    Пошук даних в таблиці '{table_name}' для: '{log_value}'...")

    cursor.execute(full_query, params)
    result = cursor.fetchone()

    if result:
        print(f"    Знайдено дані - ID '{result[0]}'")
        return result[0]
    else: # Якщо не знайдено, вставляємо новий запис
        print(f"    Не знайдено даних - вставка нових даних.")
        if table_name == "recommended_areas":
            insert_query = f"INSERT INTO conditioners.{table_name} (area_sqm) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (value,))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        
        elif table_name == "unit_weights":
            insert_query = f"""
            INSERT INTO conditioners.unit_weights (net_kg, gross_kg)
            VALUES (%s, %s) RETURNING {id_column};
            """
            cursor.execute(insert_query, (kwargs["net_kg"], kwargs["gross_kg"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id

        elif table_name == "unit_component_properties":
            insert_query = f"""
            INSERT INTO conditioners.unit_component_properties (
                length_mm, depth_mm, height_mm, packed_length_mm, packed_depth_mm, packed_height_mm, component_type_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING {id_column};
            """
            cursor.execute(insert_query, (
                value, # length_mm
                kwargs["depth_mm"],
                kwargs["height_mm"],
                kwargs.get("packed_length_mm"),
                kwargs.get("packed_depth_mm"),
                kwargs.get("packed_height_mm"),
                kwargs["component_type_id"]
            ))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        
        elif table_name == "brands":
            insert_query = f"INSERT INTO conditioners.brands (brand_name) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["brand_name"],))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "conditioner_types":
            insert_query = f"INSERT INTO conditioners.conditioner_types (type_name_ukr, type_name_eng) VALUES (%s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["type_name_ukr"], kwargs.get("type_name_eng")))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "conditioner_energy_efficiency":
            insert_query = f"INSERT INTO conditioners.conditioner_energy_efficiency (class_name) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["class_name"],))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "conditioner_model_names":
            insert_query = f"INSERT INTO conditioners.conditioner_model_names (model_name_ukr, model_name_eng) VALUES (%s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["model_name_ukr"], kwargs.get("model_name_eng")))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "internal_units":
            insert_query = f"INSERT INTO conditioners.internal_units (unit_name) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (value,))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "external_units":
            insert_query = f"INSERT INTO conditioners.external_units (unit_name) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (value,))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        # --- НОВЕ: для панелей ---
        elif table_name == "panels":
            insert_query = f"INSERT INTO conditioners.panels (model_name) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (value,))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "compressor_manufacturers":
            insert_query = f"INSERT INTO conditioners.compressor_manufacturers (manufacturer_name) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["manufacturer_name"],))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "compressor_types":
            insert_query = f"INSERT INTO conditioners.compressor_types (type_name_ukr) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["type_name_ukr"],))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "refrigerant_types":
            insert_query = f"INSERT INTO conditioners.refrigerant_types (type_name) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["type_name"],))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "warranty_periods":
            insert_query = f"INSERT INTO conditioners.warranty_periods (years) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["years"],))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "operation_modes":
            insert_query = f"INSERT INTO conditioners.operation_modes (mode_name_ukr) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["mode_name_ukr"],))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "allowed_voltage_ranges":
            insert_query = f"INSERT INTO conditioners.allowed_voltage_ranges (min_voltage, max_voltage, unit) VALUES (%s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["max_voltage"], kwargs["unit"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        # --- НОВЕ: для voltage_frequency_phases ---
        elif table_name == "voltage_frequency_phases":
            insert_query = f"INSERT INTO conditioners.voltage_frequency_phases (voltage_range, phase, frequency_hz) VALUES (%s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["phase"], kwargs["frequency_hz"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "temperature_setting_ranges":
            insert_query = f"INSERT INTO conditioners.temperature_setting_ranges (min_temp_celsius, max_temp_celsius) VALUES (%s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["max_temp_celsius"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "indoor_operating_temp_ranges":
            insert_query = f"INSERT INTO conditioners.indoor_operating_temp_ranges (cooling_min_celsius, cooling_max_celsius, heating_min_celsius, heating_max_celsius) VALUES (%s, %s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["cooling_max_celsius"], kwargs["heating_min_celsius"], kwargs["heating_max_celsius"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "outdoor_operating_temp_ranges":
            insert_query = f"INSERT INTO conditioners.outdoor_operating_temp_ranges (cooling_min_celsius, cooling_max_celsius, heating_min_celsius, heating_max_celsius) VALUES (%s, %s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["cooling_max_celsius"], kwargs["heating_min_celsius"], kwargs["heating_max_celsius"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "watt_specs":
            insert_query = f"INSERT INTO conditioners.watt_specs (nominal_watt_value, min_watt_value, max_watt_value, operation_mode_id) VALUES (%s, %s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["min_watt_value"], kwargs["max_watt_value"], kwargs["operation_mode_id"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "btu_specs":
            insert_query = f"INSERT INTO conditioners.btu_specs (nominal_btu_value, min_btu_value, max_btu_value, operation_mode_id) VALUES (%s, %s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["min_btu_value"], kwargs["max_btu_value"], kwargs["operation_mode_id"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "power_consumption_specs":
            insert_query = f"INSERT INTO conditioners.power_consumption_specs (nominal_consumption_watt, min_consumption_watt, max_consumption_watt, operation_mode_id) VALUES (%s, %s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["min_consumption_watt"], kwargs["max_consumption_watt"], kwargs["operation_mode_id"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "current_specs":
            insert_query = f"INSERT INTO conditioners.current_specs (nominal_current_amp, min_current_amp, max_current_amp, operation_mode_id) VALUES (%s, %s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["min_current_amp"], kwargs["max_current_amp"], kwargs["operation_mode_id"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "energy_efficiency_specs":
            if "seer" in kwargs and kwargs["seer"] is not None:
                insert_query = f"INSERT INTO conditioners.energy_efficiency_specs (seer, operation_mode_id, energy_efficiency_class_id) VALUES (%s, %s, %s) RETURNING {id_column};"
                cursor.execute(insert_query, (kwargs["seer"], kwargs["operation_mode_id"], kwargs["energy_efficiency_class_id"]))
            elif "scop" in kwargs and kwargs["scop"] is not None:
                insert_query = f"INSERT INTO conditioners.energy_efficiency_specs (scop, operation_mode_id, energy_efficiency_class_id) VALUES (%s, %s, %s) RETURNING {id_column};"
                cursor.execute(insert_query, (kwargs["scop"], kwargs["operation_mode_id"], kwargs["energy_efficiency_class_id"]))
            else:
                return None
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "indoor_air_flow_specs":
            insert_query = f"INSERT INTO conditioners.indoor_air_flow_specs (high_cmh, medium_cmh, low_cmh) VALUES (%s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["medium_cmh"], kwargs["low_cmh"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "max_electrical_specs":
            insert_query = f"INSERT INTO conditioners.max_electrical_specs (max_power_consumption_watt, max_current_amp) VALUES (%s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["max_current_amp"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "indoor_noise_levels":
            insert_query = f"INSERT INTO conditioners.indoor_noise_levels (high_db, medium_db, low_db, sleep_db) VALUES (%s, %s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["medium_db"], kwargs["low_db"], kwargs.get("sleep_db")))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "outdoor_air_flow_specs":
            insert_query = f"INSERT INTO conditioners.outdoor_air_flow_specs (volume_cmh) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (value,))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "outdoor_noise_levels":
            insert_query = f"INSERT INTO conditioners.outdoor_noise_levels (db_value) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (value,))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "refrigerant_charges":
            insert_query = f"INSERT INTO conditioners.refrigerant_charges (weight_kg, oil_volume_ml, oil_type) VALUES (%s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["oil_volume_ml"], kwargs["oil_type"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "refrigerant_pipe_specs":
            insert_query = f"INSERT INTO conditioners.refrigerant_pipe_specs (liquid_line_mm, liquid_line_inch, gas_line_mm, gas_line_inch, max_length_m, max_height_diff_m) VALUES (%s, %s, %s, %s, %s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (value, kwargs["liquid_inch"], kwargs["gas_mm"], kwargs["gas_inch"], kwargs["max_length"], kwargs["max_height_diff"]))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "power_supply_locations":
            insert_query = f"INSERT INTO conditioners.power_supply_locations (location_name_ukr, location_name_eng) VALUES (%s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["location_name_ukr"], kwargs.get("location_name_eng")))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "power_cables_specs":
            power_cable_mm2 = str(kwargs["power_cable_mm2"]).replace('×', 'x') if kwargs.get("power_cable_mm2") is not None else None
            interconnect_cable_mm2 = str(kwargs["interconnect_cable_mm2"]).replace('×', 'x') if kwargs.get("interconnect_cable_mm2") is not None else None
            insert_query = f"INSERT INTO conditioners.power_cables_specs (power_cable_mm2, interconnect_cable_mm2) VALUES (%s, %s) RETURNING {id_column};"
            cursor.execute(insert_query, (power_cable_mm2, interconnect_cable_mm2))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        elif table_name == "component_types":
            insert_query = f"INSERT INTO conditioners.component_types (type_name_ukr) VALUES (%s) RETURNING {id_column};"
            cursor.execute(insert_query, (kwargs["type_name_ukr"],))
            new_id = cursor.fetchone()[0]
            print(f"    Вставлено нові дані - ID '{new_id}'")
            return new_id
        
        return None # Якщо не було знайдено або вставлено ID, повертаємо None


def insert_data():
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        cur = conn.cursor()

        print("--- Пошук та/або вставка загальних довідкових даних ---")
        brand_id = get_id_from_db(cur, "brands", "brand_id", None, brand_name="NC Clima")
        
        # --- ЗМІНА: тип кондиціонера тепер "Касетний" ---
        type_id = get_id_from_db(cur, "conditioner_types", "conditioner_type_id", None, type_name_ukr="Касетний", type_name_eng="Cassette")
        
        temp_setting_range_id = get_id_from_db(cur, "temperature_setting_ranges", "temp_setting_id", 16, max_temp_celsius=30)
        # --- ЗМІНА: діапазони температур можуть відрізнятися для касетних ---
        indoor_op_temp_range_id = get_id_from_db(cur, "indoor_operating_temp_ranges", "op_temp_range_id", -15, cooling_max_celsius=50, heating_min_celsius=-15, heating_max_celsius=50)
        outdoor_op_temp_range_id = get_id_from_db(cur, "outdoor_operating_temp_ranges", "op_temp_range_id", -25, cooling_max_celsius=24, heating_min_celsius=-25, heating_max_celsius=24) # Уточнено за новими даними
        
        # Compressor manufacturer тепер "GMCC"
        # ВИПРАВЛЕНО ТУТ: manufacturer_id на compressor_manufacturer_id
        compressor_manufacturer_id = get_id_from_db(cur, "compressor_manufacturers", "compressor_manufacturer_id", None, manufacturer_name="GMCC")
        
        # Compressor type залишаємо "Інверторний"
        compressor_type_id = get_id_from_db(cur, "compressor_types", "type_id", None, type_name_ukr="Інверторний")
        
        refrigerant_type_id = get_id_from_db(cur, "refrigerant_types", "type_id", None, type_name="R32")
        warranty_period_id = get_id_from_db(cur, "warranty_periods", "warranty_period_id", None, years=2)

        cooling_mode_id = get_id_from_db(cur, "operation_modes", "operation_mode_id", None, mode_name_ukr="Охолодження")
        heating_mode_id = get_id_from_db(cur, "operation_modes", "operation_mode_id", None, mode_name_ukr="Обігрів")
        
        # Компонентні типи (для unit_component_properties)
        indoor_component_type_id = get_id_from_db(cur, "component_types", "component_type_id", None, type_name_ukr="Внутрішній блок")
        outdoor_component_type_id = get_id_from_db(cur, "component_types", "component_type_id", None, type_name_ukr="Зовнішній блок")
        panel_component_type_id = get_id_from_db(cur, "component_types", "component_type_id", None, type_name_ukr="Панель")


        print(f"\nЗагальні ID: Brand ID: {brand_id}, Type ID: {type_id}")
        print("--------------------------------------------------")

        for unit_code, data in conditioner_data.items():
            print(f"\n--- Обробка моделі: {data['model_name_ukr']} ({unit_code}) ---")

            # Отримуємо ID для всіх довідкових даних
            model_name_id = get_id_from_db(cur, "conditioner_model_names", "model_name_id", None,
                                            model_name_ukr=data["model_name_ukr"], model_name_eng=data["model_name_eng"])
            internal_unit_id = get_id_from_db(cur, "internal_units", "internal_unit_id", data["internal_unit_name"])
            external_unit_id = get_id_from_db(cur, "external_units", "external_unit_id", data["external_unit_name"])
            
            # --- НОВЕ: Панель ---
            panel_id = get_id_from_db(cur, "panels", "panel_id", data["panel_props"]["model"])

            # Енергоефективність
            cooling_ee_class_id = get_id_from_db(cur, "conditioner_energy_efficiency", "energy_efficiency_id", None, class_name=data["cooling"]["energy_efficiency"]["class_name"])
            heating_ee_class_id = get_id_from_db(cur, "conditioner_energy_efficiency", "energy_efficiency_id", None, class_name=data["heating"]["energy_efficiency"]["class_name"])


            # Cooling Specs
            cooling_watt_specs_id = get_id_from_db(cur, "watt_specs", "watt_specs_id", data["cooling"]["watt"]["nominal"],
                                                    min_watt_value=data["cooling"]["watt"]["min"],
                                                    max_watt_value=data["cooling"]["watt"]["max"],
                                                    operation_mode_id=cooling_mode_id)
            cooling_btu_specs_id = get_id_from_db(cur, "btu_specs", "btu_specs_id", data["cooling"]["btu"]["nominal"],
                                                  min_btu_value=data["cooling"]["btu"]["min"],
                                                  max_btu_value=data["cooling"]["btu"]["max"],
                                                  operation_mode_id=cooling_mode_id)
            cooling_power_consumption_specs_id = get_id_from_db(cur, "power_consumption_specs", "power_consumption_specs_id",
                                                                 data["cooling"]["power_consumption"]["nominal"],
                                                                 min_consumption_watt=data["cooling"]["power_consumption"]["min"],
                                                                 max_consumption_watt=data["cooling"]["power_consumption"]["max"],
                                                                 operation_mode_id=cooling_mode_id)
            cooling_current_specs_id = get_id_from_db(cur, "current_specs", "current_specs_id", data["cooling"]["current"]["nominal"],
                                                      min_current_amp=data["cooling"]["current"]["min"],
                                                      max_current_amp=data["cooling"]["current"]["max"],
                                                      operation_mode_id=cooling_mode_id)
            cooling_energy_efficiency_specs_id = get_id_from_db(cur, "energy_efficiency_specs", "energy_efficiency_specs_id", None,
                                                                 seer=data["cooling"]["energy_efficiency"]["seer"],
                                                                 operation_mode_id=cooling_mode_id,
                                                                 energy_efficiency_class_id=cooling_ee_class_id)
            
            # Heating Specs
            heating_watt_specs_id = get_id_from_db(cur, "watt_specs", "watt_specs_id", data["heating"]["watt"]["nominal"],
                                                    min_watt_value=data["heating"]["watt"]["min"],
                                                    max_watt_value=data["heating"]["watt"]["max"],
                                                    operation_mode_id=heating_mode_id)
            heating_btu_specs_id = get_id_from_db(cur, "btu_specs", "btu_specs_id", data["heating"]["btu"]["nominal"],
                                                  min_btu_value=data["heating"]["btu"]["min"],
                                                  max_btu_value=data["heating"]["btu"]["max"],
                                                  operation_mode_id=heating_mode_id)
            heating_power_consumption_specs_id = get_id_from_db(cur, "power_consumption_specs", "power_consumption_specs_id",
                                                                 data["heating"]["power_consumption"]["nominal"],
                                                                 min_consumption_watt=data["heating"]["power_consumption"]["min"],
                                                                 max_consumption_watt=data["heating"]["power_consumption"]["max"],
                                                                 operation_mode_id=heating_mode_id)
            heating_current_specs_id = get_id_from_db(cur, "current_specs", "current_specs_id", data["heating"]["current"]["nominal"],
                                                      min_current_amp=data["heating"]["current"]["min"],
                                                      max_current_amp=data["heating"]["current"]["max"],
                                                      operation_mode_id=heating_mode_id)
            heating_energy_efficiency_specs_id = get_id_from_db(cur, "energy_efficiency_specs", "energy_efficiency_specs_id", None,
                                                                 scop=data["heating"]["energy_efficiency"]["scop"],
                                                                 operation_mode_id=heating_mode_id,
                                                                 energy_efficiency_class_id=heating_ee_class_id)
            
            indoor_air_flow_id = get_id_from_db(cur, "indoor_air_flow_specs", "air_flow_id", data["indoor_airflow"]["high"],
                                                  medium_cmh=data["indoor_airflow"]["medium"],
                                                  low_cmh=data["indoor_airflow"]["low"])

            max_electrical_specs_id = get_id_from_db(cur, "max_electrical_specs", "max_electrical_specs_id", data["max_electrical_specs"]["power"],
                                                      max_current_amp=data["max_electrical_specs"]["current"])

            indoor_noise_level_id = get_id_from_db(cur, "indoor_noise_levels", "indoor_noise_level_id", data["indoor_noise"]["high"],
                                                    medium_db=data["indoor_noise"]["medium"],
                                                    low_db=data["indoor_noise"]["low"],
                                                    sleep_db=data["indoor_noise"].get("sleep")) # Використовуємо .get для sleep_db, бо може бути відсутній
            
            # --- Отримуємо ID ваги для внутрішнього блоку ---
            indoor_weight_id = get_id_from_db(cur, "unit_weights", "weight_id", None,
                                              net_kg=data["indoor_unit_props"]["net_kg"],
                                              gross_kg=data["indoor_unit_props"]["gross_kg"])

            # --- Отримуємо ID властивостей розмірів для внутрішнього блоку ---
            indoor_unit_properties_id = get_id_from_db(cur, "unit_component_properties", "property_id", data["indoor_unit_props"]["length"],
                                                         depth_mm=data["indoor_unit_props"]["depth"],
                                                         height_mm=data["indoor_unit_props"]["height"],
                                                         packed_length_mm=data["indoor_unit_props"]["packed_length"],
                                                         packed_depth_mm=data["indoor_unit_props"]["packed_depth"],
                                                         packed_height_mm=data["indoor_unit_props"]["packed_height"],
                                                         component_type_id=indoor_component_type_id) # Використовуємо ID компонента

            # --- НОВЕ: Отримуємо ID ваги для панелі ---
            panel_weight_id = get_id_from_db(cur, "unit_weights", "weight_id", None,
                                             net_kg=data["panel_props"]["net_kg"],
                                             gross_kg=data["panel_props"]["gross_kg"])
            
            # --- НОВЕ: Отримуємо ID властивостей розмірів для панелі ---
            panel_properties_id = get_id_from_db(cur, "unit_component_properties", "property_id", data["panel_props"]["length"],
                                                  depth_mm=data["panel_props"]["depth"],
                                                  height_mm=data["panel_props"]["height"],
                                                  packed_length_mm=data["panel_props"]["packed_length"],
                                                  packed_depth_mm=data["panel_props"]["packed_depth"],
                                                  packed_height_mm=data["panel_props"]["packed_height"],
                                                  component_type_id=panel_component_type_id) # Використовуємо ID компонента

            outdoor_air_flow_id = get_id_from_db(cur, "outdoor_air_flow_specs", "air_flow_id", data["outdoor_airflow_specs"]["volume"])

            outdoor_noise_level_id = get_id_from_db(cur, "outdoor_noise_levels", "outdoor_noise_level_id", data["outdoor_noise_levels"]["db_value"])
            
            # --- Отримуємо ID ваги для зовнішнього блоку ---
            outdoor_weight_id = get_id_from_db(cur, "unit_weights", "weight_id", None,
                                               net_kg=data["outdoor_unit_props"]["net_kg"],
                                               gross_kg=data["outdoor_unit_props"]["gross_kg"])

            # --- Отримуємо ID властивостей розмірів для зовнішнього блоку ---
            outdoor_unit_properties_id = get_id_from_db(cur, "unit_component_properties", "property_id", data["outdoor_unit_props"]["length"],
                                                          depth_mm=data["outdoor_unit_props"]["depth"],
                                                          height_mm=data["outdoor_unit_props"]["height"],
                                                          packed_length_mm=data["outdoor_unit_props"]["packed_length"],
                                                          packed_depth_mm=data["outdoor_unit_props"]["packed_depth"],
                                                          packed_height_mm=data["outdoor_unit_props"]["packed_height"],
                                                          component_type_id=outdoor_component_type_id) # Використовуємо ID компонента
            
            refrigerant_charge_id = get_id_from_db(cur, "refrigerant_charges", "charge_id", data["refrigerant_charge"]["weight"],
                                                    oil_volume_ml=data["refrigerant_charge"]["oil_volume"],
                                                    oil_type=data["refrigerant_charge"]["oil_type"])

            refrigerant_pipe_specs_id = get_id_from_db(cur, "refrigerant_pipe_specs", "pipe_specs_id", data["refrigerant_pipe_specs"]["liquid_mm"],
                                                        liquid_inch=data["refrigerant_pipe_specs"]["liquid_inch"],
                                                        gas_mm=data["refrigerant_pipe_specs"]["gas_mm"],
                                                        gas_inch=data["refrigerant_pipe_specs"]["gas_inch"],
                                                        max_length=data["refrigerant_pipe_specs"]["max_length"],
                                                        max_height_diff=data["refrigerant_pipe_specs"]["max_height_diff"])
            
            primary_power_supply_location_id = get_id_from_db(cur, "power_supply_locations", "location_id", None,
                                                                location_name_ukr=data["primary_power_supply_location"],
                                                                location_name_eng="Outdoor unit") # Додано англійську назву для уніфікації

            power_cables_specs_id = get_id_from_db(cur, "power_cables_specs", "cable_specs_id", None,
                                                    power_cable_mm2=data["power_cables_specs"]["power_cable"],
                                                    interconnect_cable_mm2=data["power_cables_specs"]["interconnect_cable"])

            # Отримуємо ID для живлення внутрішнього блоку
            indoor_power_supply_vfp_id = get_id_from_db(cur, "voltage_frequency_phases", "vfp_id",
                                                          data["power_supply_indoor"]["voltage"],
                                                          phase=data["power_supply_indoor"]["phase"],
                                                          frequency_hz=data["power_supply_indoor"]["frequency"])
            
            # Отримуємо ID для живлення зовнішнього блоку
            outdoor_power_supply_vfp_id = get_id_from_db(cur, "voltage_frequency_phases", "vfp_id",
                                                           data["power_supply_outdoor"]["voltage"],
                                                           phase=data["power_supply_outdoor"]["phase"],
                                                           frequency_hz=data["power_supply_outdoor"]["frequency"])
            
            recommended_area_id = None
            if data.get("recommended_area_sqm") is not None:
                recommended_area_id = get_id_from_db(cur, "recommended_areas", "recommended_area_id", data["recommended_area_sqm"])
            
            # --- UPSERT логіка для conditioner_models ---
            insert_or_update_query = """
            INSERT INTO conditioners.conditioner_models (
                brand_id, conditioner_type_id, model_name_id, internal_unit_id, external_unit_id, panel_id,
                cooling_watt_specs_id, heating_watt_specs_id, 
                cooling_btu_specs_id, heating_btu_specs_id,
                cooling_power_consumption_specs_id, heating_power_consumption_specs_id,
                cooling_current_specs_id, heating_current_specs_id,
                cooling_energy_efficiency_specs_id, heating_energy_efficiency_specs_id,
                indoor_air_flow_id, max_electrical_specs_id, 
                indoor_noise_level_id, indoor_unit_properties_id, panel_properties_id, 
                outdoor_air_flow_id, outdoor_noise_level_id,
                outdoor_unit_properties_id, compressor_manufacturer_id, compressor_type_id,
                refrigerant_type_id, refrigerant_charge_id, refrigerant_pipe_specs_id,
                primary_power_supply_location_id, power_cables_specs_id, 
                indoor_power_supply_vfp_id, outdoor_power_supply_vfp_id,
                temperature_setting_range_id, indoor_operating_temp_range_id, outdoor_operating_temp_range_id,
                recommended_area_id, status, last_updated,
                indoor_weight_id, outdoor_weight_id, panel_weight_id, warranty_period_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (model_name_id) DO UPDATE SET -- Припускаємо, що model_name_id унікальний для моделі
                brand_id = EXCLUDED.brand_id,
                conditioner_type_id = EXCLUDED.conditioner_type_id,
                internal_unit_id = EXCLUDED.internal_unit_id,
                external_unit_id = EXCLUDED.external_unit_id,
                panel_id = EXCLUDED.panel_id,
                cooling_watt_specs_id = EXCLUDED.cooling_watt_specs_id,
                heating_watt_specs_id = EXCLUDED.heating_watt_specs_id,
                cooling_btu_specs_id = EXCLUDED.cooling_btu_specs_id,
                heating_btu_specs_id = EXCLUDED.heating_btu_specs_id,
                cooling_power_consumption_specs_id = EXCLUDED.cooling_power_consumption_specs_id,
                heating_power_consumption_specs_id = EXCLUDED.heating_power_consumption_specs_id,
                cooling_current_specs_id = EXCLUDED.cooling_current_specs_id,
                heating_current_specs_id = EXCLUDED.heating_current_specs_id,
                cooling_energy_efficiency_specs_id = EXCLUDED.cooling_energy_efficiency_specs_id,
                heating_energy_efficiency_specs_id = EXCLUDED.heating_energy_efficiency_specs_id,
                indoor_air_flow_id = EXCLUDED.indoor_air_flow_id,
                max_electrical_specs_id = EXCLUDED.max_electrical_specs_id,
                indoor_noise_level_id = EXCLUDED.indoor_noise_level_id,
                indoor_unit_properties_id = EXCLUDED.indoor_unit_properties_id,
                panel_properties_id = EXCLUDED.panel_properties_id,
                outdoor_air_flow_id = EXCLUDED.outdoor_air_flow_id,
                outdoor_noise_level_id = EXCLUDED.outdoor_noise_level_id,
                outdoor_unit_properties_id = EXCLUDED.outdoor_unit_properties_id,
                compressor_manufacturer_id = EXCLUDED.compressor_manufacturer_id,
                compressor_type_id = EXCLUDED.compressor_type_id,
                refrigerant_type_id = EXCLUDED.refrigerant_type_id,
                refrigerant_charge_id = EXCLUDED.refrigerant_charge_id,
                refrigerant_pipe_specs_id = EXCLUDED.refrigerant_pipe_specs_id,
                primary_power_supply_location_id = EXCLUDED.primary_power_supply_location_id,
                power_cables_specs_id = EXCLUDED.power_cables_specs_id,
                indoor_power_supply_vfp_id = EXCLUDED.indoor_power_supply_vfp_id,
                outdoor_power_supply_vfp_id = EXCLUDED.outdoor_power_supply_vfp_id,
                temperature_setting_range_id = EXCLUDED.temperature_setting_range_id,
                indoor_operating_temp_range_id = EXCLUDED.indoor_operating_temp_range_id,
                outdoor_operating_temp_range_id = EXCLUDED.outdoor_operating_temp_range_id,
                recommended_area_id = EXCLUDED.recommended_area_id,
                status = EXCLUDED.status,
                last_updated = EXCLUDED.last_updated,
                indoor_weight_id = EXCLUDED.indoor_weight_id,
                outdoor_weight_id = EXCLUDED.outdoor_weight_id,
                panel_weight_id = EXCLUDED.panel_weight_id,
                warranty_period_id = EXCLUDED.warranty_period_id
            RETURNING model_id;
            """
            # Параметри для вставки/оновлення
            params = (
                brand_id, type_id, model_name_id, internal_unit_id, external_unit_id, panel_id,
                cooling_watt_specs_id, heating_watt_specs_id,
                cooling_btu_specs_id, heating_btu_specs_id,
                cooling_power_consumption_specs_id, heating_power_consumption_specs_id,
                cooling_current_specs_id, heating_current_specs_id,
                cooling_energy_efficiency_specs_id, heating_energy_efficiency_specs_id,
                indoor_air_flow_id, max_electrical_specs_id, 
                indoor_noise_level_id, indoor_unit_properties_id, panel_properties_id,
                outdoor_air_flow_id, outdoor_noise_level_id,
                outdoor_unit_properties_id, compressor_manufacturer_id, compressor_type_id,
                refrigerant_type_id, refrigerant_charge_id, refrigerant_pipe_specs_id,
                primary_power_supply_location_id, power_cables_specs_id,
                indoor_power_supply_vfp_id, outdoor_power_supply_vfp_id,
                temp_setting_range_id, indoor_op_temp_range_id, outdoor_op_temp_range_id,
                recommended_area_id, "Active", datetime.now(),
                indoor_weight_id, outdoor_weight_id, panel_weight_id, warranty_period_id
            )
            
            cur.execute(insert_or_update_query, params)
            new_model_id = cur.fetchone()[0]
            print(f"--- Модель {data['model_name_ukr']} успішно оновлена/додана з ID: {new_model_id} ---")

        conn.commit()
        print("\nВсі дані оброблено успішно.")

    except (Exception, psycopg2.Error) as error:
        print(f"Помилка при роботі з PostgreSQL: {error}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("З'єднання з базою даних закрито.")

if __name__ == "__main__":
    # Тут мають бути визначені DB_CONNECTION_STRING та conditioner_data
    # для того, щоб скрипт міг бути запущений без помилок.
    # Наприклад:
    # DB_CONNECTION_STRING = "host=localhost dbname=your_db user=your_user password=your_password"
    # conditioner_data = {
    #     "YOUR_UNIT_CODE": {
    #         "model_name_ukr": "...",
    #         "model_name_eng": "...",
    #         # ... інші дані
    #     }
    # }
    insert_data()
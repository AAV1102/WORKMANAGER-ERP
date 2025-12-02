<?php
/**
 * Auto Import Inventory PHP Script for WORKMANAGER ERP
 * This script automatically imports inventory data and updates all related tabs
 */

class AutoInventoryImporter {
    private $db;
    private $stats = [
        'equipos_agrupados' => 0,
        'equipos_individuales' => 0,
        'inventario_general' => 0,
        'equipos_asignados' => 0,
        'equipos_baja' => 0,
        'tandas_nuevas' => 0
    ];

    public function __construct($db_host = 'localhost', $db_user = 'root', $db_pass = '', $db_name = 'workmanager_erp') {
        try {
            $this->db = new PDO("mysql:host=$db_host;dbname=$db_name;charset=utf8", $db_user, $db_pass);
            $this->db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } catch(PDOException $e) {
            die("Connection failed: " . $e->getMessage());
        }
    }

    public function importEquiposAgrupados($data) {
        $stmt = $this->db->prepare("
            INSERT INTO equipos_agrupados
            (codigo_barras_unificado, nit, sede_id, asignado_anterior, asignado_actual,
             descripcion_general, estado_general, creador_registro, fecha_creacion,
             trazabilidad_soporte, documentos_entrega, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
            asignado_actual = VALUES(asignado_actual),
            estado_general = VALUES(estado_general),
            trazabilidad_soporte = VALUES(trazabilidad_soporte),
            documentos_entrega = VALUES(documentos_entrega),
            observaciones = VALUES(observaciones)
        ");

        foreach ($data as $item) {
            try {
                $stmt->execute([
                    $item['codigo_barras_unificado'] ?? null,
                    $item['nit'] ?? '901.234.567-8',
                    $item['sede_id'] ?? null,
                    $item['asignado_anterior'] ?? null,
                    $item['asignado_actual'] ?? null,
                    $item['descripcion_general'] ?? null,
                    $item['estado_general'] ?? 'disponible',
                    $item['creador_registro'] ?? 'AUTO_IMPORT',
                    $item['fecha_creacion'] ?? date('Y-m-d H:i:s'),
                    $item['trazabilidad_soporte'] ?? null,
                    $item['documentos_entrega'] ?? null,
                    $item['observaciones'] ?? null
                ]);
                $this->stats['equipos_agrupados']++;
            } catch(Exception $e) {
                error_log("Error importing equipo agrupado: " . $e->getMessage());
            }
        }
    }

    public function importEquiposIndividuales($data) {
        $stmt = $this->db->prepare("
            INSERT INTO equipos_individuales
            (codigo_barras_individual, entrada_oc_compra, cargado_nit, ciudad,
             tecnologia, serial, modelo, anterior_asignado, placa, marca, procesador,
             arch_ram, cantidad_ram, tipo_disco, espacio_disco, so, estado,
             asignado_nuevo, fecha, fecha_llegada, area, marca_monitor, modelo_monitor,
             serial_monitor, placa_monitor, proveedor, oc, observaciones, disponible,
             sede_id, creador_registro, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
            asignado_nuevo = VALUES(asignado_nuevo),
            estado = VALUES(estado),
            observaciones = VALUES(observaciones)
        ");

        foreach ($data as $item) {
            try {
                $stmt->execute([
                    $item['codigo_barras_individual'] ?? null,
                    $item['entrada_oc_compra'] ?? null,
                    $item['cargado_nit'] ?? null,
                    $item['ciudad'] ?? null,
                    $item['tecnologia'] ?? null,
                    $item['serial'] ?? null,
                    $item['modelo'] ?? null,
                    $item['anterior_asignado'] ?? null,
                    $item['placa'] ?? null,
                    $item['marca'] ?? null,
                    $item['procesador'] ?? null,
                    $item['arch_ram'] ?? null,
                    $item['cantidad_ram'] ?? null,
                    $item['tipo_disco'] ?? null,
                    $item['espacio_disco'] ?? null,
                    $item['so'] ?? null,
                    $item['estado'] ?? 'disponible',
                    $item['asignado_nuevo'] ?? null,
                    $item['fecha'] ?? null,
                    $item['fecha_llegada'] ?? null,
                    $item['area'] ?? null,
                    $item['marca_monitor'] ?? null,
                    $item['modelo_monitor'] ?? null,
                    $item['serial_monitor'] ?? null,
                    $item['placa_monitor'] ?? null,
                    $item['proveedor'] ?? null,
                    $item['oc'] ?? null,
                    $item['observaciones'] ?? null,
                    $item['disponible'] ?? 'Si',
                    $item['sede_id'] ?? null,
                    $item['creador_registro'] ?? 'AUTO_IMPORT',
                    $item['fecha_creacion'] ?? date('Y-m-d H:i:s')
                ]);
                $this->stats['equipos_individuales']++;
            } catch(Exception $e) {
                error_log("Error importing equipo individual: " . $e->getMessage());
            }
        }
    }

    public function importInventarioGeneral($data) {
        if (isset($data['agrupados'])) {
            $this->importEquiposAgrupados($data['agrupados']);
        }
        if (isset($data['individuales'])) {
            $this->importEquiposIndividuales($data['individuales']);
        }
        $this->stats['inventario_general'] = $this->stats['equipos_agrupados'] + $this->stats['equipos_individuales'];
    }

    public function importEquiposAsignados($data) {
        foreach ($data as $item) {
            try {
                // Update equipos_individuales
                $stmt1 = $this->db->prepare("
                    UPDATE equipos_individuales
                    SET asignado_nuevo = ?, estado = 'asignado'
                    WHERE codigo_barras_individual = ?
                ");
                $stmt1->execute([$item['asignado_a'] ?? null, $item['codigo'] ?? null]);

                // Update equipos_agrupados
                $stmt2 = $this->db->prepare("
                    UPDATE equipos_agrupados
                    SET asignado_actual = ?, estado_general = 'asignado'
                    WHERE codigo_barras_unificado = ?
                ");
                $stmt2->execute([$item['asignado_a'] ?? null, $item['codigo'] ?? null]);

                $this->stats['equipos_asignados']++;
            } catch(Exception $e) {
                error_log("Error importing equipo asignado: " . $e->getMessage());
            }
        }
    }

    public function importEquiposBaja($data) {
        $stmt = $this->db->prepare("
            INSERT INTO inventario_bajas
            (equipo_id, tipo_inventario, motivo_baja, fecha_baja, responsable_baja,
             documentos_soporte, fotografias_soporte, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ");

        foreach ($data as $item) {
            try {
                $stmt->execute([
                    $item['equipo_id'] ?? null,
                    $item['tipo_inventario'] ?? null,
                    $item['motivo_baja'] ?? null,
                    date('Y-m-d H:i:s'),
                    $item['responsable_baja'] ?? null,
                    $item['documentos_soporte'] ?? null,
                    $item['fotografias_soporte'] ?? null,
                    $item['observaciones'] ?? null
                ]);

                // Update status to baja
                $stmt_update = $this->db->prepare("
                    UPDATE equipos_individuales SET estado = 'baja' WHERE id = ?
                ");
                $stmt_update->execute([$item['equipo_id'] ?? null]);

                $this->stats['equipos_baja']++;
            } catch(Exception $e) {
                error_log("Error importing equipo baja: " . $e->getMessage());
            }
        }
    }

    public function importTandasNuevas($data) {
        $stmt = $this->db->prepare("
            INSERT INTO tandas_equipos_nuevos
            (numero_tanda, descripcion, fecha_ingreso, cantidad_equipos, proveedor,
             valor_total, estado, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
            descripcion = VALUES(descripcion),
            cantidad_equipos = VALUES(cantidad_equipos),
            proveedor = VALUES(proveedor),
            valor_total = VALUES(valor_total),
            observaciones = VALUES(observaciones)
        ");

        foreach ($data as $item) {
            try {
                $stmt->execute([
                    $item['numero_tanda'] ?? null,
                    $item['descripcion'] ?? null,
                    date('Y-m-d H:i:s'),
                    $item['cantidad_equipos'] ?? null,
                    $item['proveedor'] ?? null,
                    $item['valor_total'] ?? null,
                    'en_proceso',
                    $item['observaciones'] ?? null
                ]);
                $this->stats['tandas_nuevas']++;
            } catch(Exception $e) {
                error_log("Error importing tanda nueva: " . $e->getMessage());
            }
        }
    }

    public function importFromJSON($json_file) {
        if (!file_exists($json_file)) {
            throw new Exception("File $json_file not found");
        }

        $json_content = file_get_contents($json_file);
        $data = json_decode($json_content, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception("Invalid JSON file");
        }

        error_log("Starting auto import from $json_file");

        if (isset($data['equipos_agrupados'])) {
            $this->importEquiposAgrupados($data['equipos_agrupados']);
        }
        if (isset($data['equipos_individuales'])) {
            $this->importEquiposIndividuales($data['equipos_individuales']);
        }
        if (isset($data['inventario_general'])) {
            $this->importInventarioGeneral($data['inventario_general']);
        }
        if (isset($data['equipos_asignados'])) {
            $this->importEquiposAsignados($data['equipos_asignados']);
        }
        if (isset($data['equipos_baja'])) {
            $this->importEquiposBaja($data['equipos_baja']);
        }
        if (isset($data['tandas_nuevas'])) {
            $this->importTandasNuevas($data['tandas_nuevas']);
        }

        error_log("Auto import completed. Stats: " . json_encode($this->stats));
        return $this->stats;
    }

    public function getStats() {
        return $this->stats;
    }
}

// Usage example
if ($argc < 2) {
    echo "Usage: php auto_import.php <json_file>\n";
    exit(1);
}

$json_file = $argv[1];

try {
    $importer = new AutoInventoryImporter();
    $result = $importer->importFromJSON($json_file);

    echo "Import completed successfully!\n";
    echo json_encode($result, JSON_PRETTY_PRINT) . "\n";
} catch(Exception $e) {
    echo "Import failed: " . $e->getMessage() . "\n";
    exit(1);
}
?>

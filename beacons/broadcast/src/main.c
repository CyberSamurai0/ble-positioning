#include <stdio.h>
#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/dsp/types.h>

#define VERSION_MAJOR '0'
#define VERSION_MINOR '1'
#define VERSION_PATCH '8'


const uint16_t building_id = 0x0001;
const uint8_t floor_number = 4;
const float16_t local_north = 1600.0f;
const float16_t local_east = 1600.0f;

#define LED0_NODE DT_ALIAS(led0)
#define LED2_NODE DT_ALIAS(led2)

static const struct gpio_dt_spec RED_LED = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
static const struct gpio_dt_spec BLUE_LED = GPIO_DT_SPEC_GET(LED2_NODE, gpios);

static const uint8_t manufacturer_data[] = {
    0xFF, 0xFF, // Company ID (0xFFFF for testing)
    'v', VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH
};

static uint8_t service_data[] = {
    // Use Indoor Positioning Service Shorthand UUID
    0x21, 0x18, // 16-bit shorthand UUID (little endian)
    (uint8_t)(building_id>>8), (uint8_t)(building_id & 0xFF), // 16-bit building ID (big endian)
    floor_number,
    0, 0, // Placeholder for two-byte local_north value
    0, 0, // Placeholder for two-byte local_east value
};

static const struct bt_data adv_payload[] = {
    BT_DATA(BT_DATA_MANUFACTURER_DATA, manufacturer_data, sizeof(manufacturer_data)),
    BT_DATA(BT_DATA_SVC_DATA16, service_data, sizeof(service_data)),
    // Optional Bluetooth display icon if we use the connectable state
    //BT_DATA_BYTES(BT_DATA_GAP_APPEARANCE, BT_BYTES_LIST_LE16(BT_APPEARANCE_SENSOR_WALL_MOUNTED)),
};

// Create a semaphore that starts a 0 with a maximum number of 1
// This allows us to delay main execution until on_bt_ready signals
// completion or 500ms elapses, whichever comes first.
// Ref: https://devzone.nordicsemi.com/guides/nrf-connect-sdk-guides/b/getting-started/posts/ncs-ble-tutorial-part-1-custom-service-in-peripheral-role#h11sk6m5kltc1breezxb93skspgqkse
static K_SEM_DEFINE(ble_init_ok, 0, 1);

/*************************
 *  Function Prototypes  *
 *************************/
// Blocks custom code execution without halting Zephyr RTOS.
// Turns on the red LED to indicate an error state.
// Uses a while true wait loop with k_sleep to avoid busy-waiting.
static void error(void);

// Callback function for when Bluetooth is ready
static void on_bt_ready(int err);


/*************************
 *  Advertising Params   *
 *************************/
// Define constants for advertising interval range
#define ADV_INTERVAL_MIN 800 // 500ms (800 * 0.625ms = 500ms)
#define ADV_INTERVAL_MAX 1600 // 1000ms (1600 * 0.625ms = 1000ms)

// REVIEW AVAILABLE OPTIONS
// Ref: https://docs.zephyrproject.org/latest/doxygen/html/group__bt__gap.html#gafbf81dab68b0e484d4742471c722fc28

// Define the parameters used to send advertisements
static const struct bt_le_adv_param *adv_params = BT_LE_ADV_PARAM(
    // Advertising options
    // Do not use BT_LE_ADV_OPT_EXT_ADV as we want backward compatibility with BLE 4.0
    //BT_LE_ADV_OPT_CONN | // Advertise as connectable
    BT_LE_ADV_OPT_SCANNABLE | // Advertise as scannable
    BT_LE_ADV_OPT_USE_IDENTITY | // Uses the true MAC rather than randomized
    BT_LE_ADV_OPT_USE_NAME,

    ADV_INTERVAL_MIN, // Minimum interval
    ADV_INTERVAL_MAX, // Maximum interval
    NULL // No peer address, use undirected advertising
);

/*************************
 *  Entrypoint Function  *
 *************************/
int main(void) {
    printk("===== BLE Positioning =====\n");
    printk("v%c.%c.%c\n", VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH);

    int err = bt_enable(on_bt_ready);

    if (err) {
        printk("Call to bt_enable in main() failed\n");
        error(); // Block further execution with error handling
    }

    // Wait up to 500ms for Bluetooth initialization to complete.
    // By using the semaphore to block execution we allow the RTOS
    // to execute other tasks while we wait.
    // Ref: https://devzone.nordicsemi.com/guides/nrf-connect-sdk-guides/b/getting-started/posts/ncs-ble-tutorial-part-1-custom-service-in-peripheral-role#h11sk6m5kltc1breezxb93skspgqkse
    err = k_sem_take(&ble_init_ok, K_MSEC(500));

    if (err) {
        printk("BLE initialization did not complete in time\n");
        error(); // Block further execution with error handling
    }

    // Convert float16_t to uint16_t for transmission
    uint16_t north_cast = 0;
    uint16_t east_cast = 0;

    memcpy(&north_cast, &local_north, sizeof(float16_t));
    memcpy(&east_cast, &local_east, sizeof(float16_t));

    // Convert uint16_t to big-endian bytes

    // Set big-endian first byte for local north
    service_data[5] = (uint8_t)(north_cast >> 8);
    // Set big-endian second byte for local north
    service_data[6] = (uint8_t)(north_cast & 0xFF);

    // Set big-endian first byte for local east
    service_data[7] = (uint8_t)(east_cast >> 8);
    // Set big-endian second byte for local east
    service_data[8] = (uint8_t)(east_cast & 0xFF);


    // Begin Advertising
    err = bt_le_adv_start(adv_params, adv_payload, ARRAY_SIZE(adv_payload), NULL, 0);

    if (err) {
        printk("Advertising failed to start (err %d)\n", err);
        error(); // Block further execution with error handling
    }

    // Turn on red LED to indicate error
    if (gpio_is_ready_dt(&BLUE_LED)) {
        gpio_pin_configure_dt(&BLUE_LED, GPIO_OUTPUT_ACTIVE);
    }
}


/***** Function Definitions *****/

// Error handling that allows Zephyr to continue running
static void error(void) {
    printk("Error!\n");

    // Turn on red LED to indicate error
    if (gpio_is_ready_dt(&RED_LED)) {
        gpio_pin_configure_dt(&RED_LED, GPIO_OUTPUT_ACTIVE);
    }

    while (1) {
        k_sleep(K_MSEC(1000));
    }
}

// Callback function for when Bluetooth is ready
static void on_bt_ready(int err) {
    if (err) {
        printk("Bluetooth init failed (err %d)\n", err);
        return;
    }

    printk("Bluetooth initialized\n");
    printk("Building %x, Floor %d\n", building_id, floor_number);
    printk("Local North: %u\n", (uint16_t)(local_north));
    printk("Local East: %u\n", (uint16_t)(local_east));

    // Signal that Bluetooth initialization is complete
    k_sem_give(&ble_init_ok);
}
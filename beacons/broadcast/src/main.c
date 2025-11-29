#include <stdio.h>
#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/drivers/gpio.h>

#define VERSION_MAJOR '0'
#define VERSION_MINOR '1'
#define VERSION_PATCH '5'

//static const POSITION[] = {1,5}; // Sample XY Coordinate System

#define LED0_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec RED_LED = GPIO_DT_SPEC_GET(LED0_NODE, gpios);

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
    // Do not use BT_LE_ADV_OPT_CONNECTABLE
    // Do not use BT_LE_ADV_OPT_EXT_ADV as we want backward compatibility
    BT_LE_ADV_OPT_SCANNABLE | 
    BT_LE_ADV_OPT_USE_NAME |
    BT_LE_ADV_OPT_USE_TX_POWER, 
    
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

    printk("Bluetooth initialized\n");
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

    // Signal that Bluetooth initialization is complete
    k_sem_give(&ble_init_ok);
}
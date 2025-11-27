#include <stdio.h>
#include <zephyr/kernel.h>

//static const POSITION[] = {1,5}; // Sample XY Coordinate System

int main(void) {
    int error = bt_enable(NULL);

    if (error) {
        printk("Bluetooth init failed (err %d)\n", error);
        return error;
    }

    printk("Bluetooth initialized\n");

    return 0;
}

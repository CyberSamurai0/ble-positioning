/*
 * Copyright (c) 2016 Intel Corporation
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

// This constant controls the blink rate (in ms)
#define SLEEP_TIME_MS   3000

// This maps to the three LED nodes in the devicetree file.
#define LED0_NODE DT_ALIAS(led0)
#define LED1_NODE DT_ALIAS(led1)
#define LED2_NODE DT_ALIAS(led2)

/*
 * A build error on this line means your board is unsupported.
 * See the sample documentation for information on how to fix this.
 */
static const struct gpio_dt_spec RED_LED = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
static const struct gpio_dt_spec GREEN_LED = GPIO_DT_SPEC_GET(LED1_NODE, gpios);
static const struct gpio_dt_spec BLUE_LED = GPIO_DT_SPEC_GET(LED2_NODE, gpios);

int main(void) {
	int ret;
	static const struct gpio_dt_spec led = BLUE_LED;
	bool led_state = true;

	if (!gpio_is_ready_dt(&led)) {
		return 0;
	}

	ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
	if (ret < 0) {
		return 0;
	}

	while (1) {
		ret = gpio_pin_toggle_dt(&led);
		if (ret < 0) {
			return 0;
		}

		led_state = !led_state;
		printf("LED state: %s\n", led_state ? "ON" : "OFF");
		k_msleep(SLEEP_TIME_MS);
	}
	return 0;
}

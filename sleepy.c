#include "nrf_drv_twi.h"
#include "app_util_platform.h"
#include "thingy52.h"
#include "bsp.h"
#include "app_timer.h"
#include "nrf_pwr_mgmt.h"
#include <math.h>
#include <stdio.h>

#define SLEEP_THRESHOLD 0.05              // Lower threshold → more accurate
#define SAMPLE_RATE 1000                 // 1 second sampling
#define WAKE_INTERVAL APP_TIMER_TICKS(3600000)  // 1 hour

#define SLEEP_TIME_THRESHOLD (60000 / SAMPLE_RATE) * 5  

APP_TIMER_DEF(m_hourly_timer);

static uint32_t sleep_counter = 0;
static uint32_t wake_counter = 0;
static bool is_sleeping = false;


static void accelerometer_event_handler(accelerometer_reading_t reading)
{
    float magnitude = sqrt(reading.x * reading.x +
                           reading.y * reading.y +
                           reading.z * reading.z);

    if (magnitude < SLEEP_THRESHOLD)
    {
        sleep_counter++;

        if (!is_sleeping && sleep_counter > SLEEP_TIME_THRESHOLD)
        {
            is_sleeping = true;
            printf("Sleep Started\n");
        }
    }
    else
    {
        wake_counter++;

        if (is_sleeping)
        {
            is_sleeping = false;
            printf("Wake Detected\n");
        }

        sleep_counter = 0;
    }
}

void hourly_timer_handler(void *p_context)
{
    uint32_t total = sleep_counter + wake_counter;

    if (total == 0)
    {
        printf("No Data Collected\n");
        return;
    }

    if (sleep_counter > total / 2)
    {
        printf("Hourly Report: Mostly Asleep\n");
    }
    else
    {
        printf("Hourly Report: Mostly Awake\n");
    }

    sleep_counter = 0;
    wake_counter = 0;
}

void power_manage(void)
{
    nrf_pwr_mgmt_run();
}

int main(void)
{
    bsp_init();
    thingy52_init();

    thingy52_accelerometer_init(accelerometer_event_handler, SAMPLE_RATE);

    app_timer_init();
    app_timer_create(&m_hourly_timer,
                     APP_TIMER_MODE_REPEATED,
                     hourly_timer_handler);

    app_timer_start(m_hourly_timer, WAKE_INTERVAL, NULL);

    nrf_pwr_mgmt_init();

    printf("Sleep Detection System Started\n");

    while (true)
    {
        power_manage();
    }
}
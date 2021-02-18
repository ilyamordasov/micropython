// pulse timer native module
// Copyright © 2020 by Thorsten von Eicken.

#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include "py/dynruntime.h"
// ESP-IDF imports
#include <esp_err.h>
#include <driver/pcnt.h>

// from smallint.h
#define MP_SMALL_INT_POSITIVE_MASK ~(WORD_MSBIT_HIGH | (WORD_MSBIT_HIGH >> 1))

extern bool mp_sched_schedule(mp_obj_t function, mp_obj_t arg);
extern void mp_hal_wake_main_task_from_isr(void);

uint8_t id;
uint8_t length;
uint32_t high_start = 0;
uint32_t low_start = 0;
uint32_t high_us = 0;
uint32_t low_us = 0;
uint32_t period_width = 0;
uint32_t period_diff = 0;
uint32_t grace = 0;
uint32_t last_period = 0;
uint8_t bit = 0;
uint8_t _cnt = 0;
uint32_t code = 0;

uint32_t mp_hal_ticks_us(void) {
    return esp_timer_get_time();
}

STATIC void GDO_isr_handler(void *arg) {
    
    //uint8_t value = gpio_get_level(id);
    _cnt ++;
    mp_obj_t handler = arg;
            mp_sched_schedule(handler, MP_OBJ_NEW_SMALL_INT(_cnt));
            mp_hal_wake_main_task_from_isr();
    //mp_printf(&mp_plat_print, "Pin: %d, Value: %d\r\n", id, value);
    //uint32_t tick = esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1);
    /*if (value == 1) {
        high_start = esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1);
        low_us = abs((esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1)) - low_start);
    }
    else if (value == 0) {
        low_start = esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1);
        high_us = abs((esp_timer_get_time() & (MICROPY_PY_UTIME_TICKS_PERIOD - 1)) - high_start);
        bit = (high_us > low_us) ? 1 : 0;
        period_width = high_us + low_us;
        period_diff = abs(last_period - period_width);
        grace = period_width / 10;
        if (period_diff > grace) {
            // start new code
            _cnt = 0;
            code = bit;
        }
        else {
            _cnt += 1;
            code <<= 1;
            code |= bit;
        }
        if (_cnt >= length-1) {
            high_start = low_start = high_us = low_us = period_width = period_diff = grace = last_period = bit = _cnt = code = 0;
            mp_obj_t handler = arg;
            mp_sched_schedule(handler, MP_OBJ_NEW_SMALL_INT(code));
            mp_hal_wake_main_task_from_isr();
        }
        else
            last_period = period_width;
    }*/
}

STATIC mp_obj_t readGDO(mp_obj_t pin, mp_obj_t handler, mp_obj_t len) {
        id = (uint)mp_obj_get_int(pin);
        length = (uint)mp_obj_get_int(len);
        esp_err_t err = gpio_isr_handler_add(id, GDO_isr_handler, (void *)handler);
        const char* ret = esp_err_to_name(err);
        return ret ? mp_obj_new_str(ret, strlen(ret)) : mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_3(readGDO_obj, readGDO);


mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
        MP_DYNRUNTIME_INIT_ENTRY
        mp_store_global(MP_QSTR_readGDO, MP_OBJ_FROM_PTR(&readGDO_obj));
        MP_DYNRUNTIME_INIT_EXIT
}

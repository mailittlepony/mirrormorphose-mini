/*
 * Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
 *
 * Distributed under terms of the MIT license.
 */

/**
 * @file overlayx.c
 * @brief
 *
 * @author Stanley Arnaud
 * @date 06/27/2025
 * @version 0
 */

// -----------------------------------------------------------------------------
// Includes
// -----------------------------------------------------------------------------
#include "overlayx.h"

#define STB_IMAGE_IMPLEMENTATION
#include "./lib/stb/stb_image.h"

#include <bcm_host.h>
#include <stdio.h>
#include <unistd.h>

// -----------------------------------------------------------------------------
// Macros and Constants
// -----------------------------------------------------------------------------
#define IMAGE_FORMAT VC_IMAGE_RGBA16

// -----------------------------------------------------------------------------
// Static Variables
// -----------------------------------------------------------------------------
static DISPMANX_DISPLAY_HANDLE_T display;
static DISPMANX_UPDATE_HANDLE_T update;
static DISPMANX_RESOURCE_HANDLE_T resource;
static DISPMANX_ELEMENT_HANDLE_T element;

static uint32_t screen_width, screen_height;
static uint16_t *image = NULL;
static int display_num = 0;

// -----------------------------------------------------------------------------
// Static Function Declarations
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Static Function Definitions
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Function Definitions
// -----------------------------------------------------------------------------
int overlay_init(const char *img_path)
{
    bcm_host_init();

    if (graphics_get_display_size(display_num, &screen_width, &screen_height) <
        0)
    {
        fprintf(stderr, "Failed to get display size\n");
        return 1;
    }

    uint32_t vc_image_ptr;
    resource = vc_dispmanx_resource_create(IMAGE_FORMAT, screen_width,
                                           screen_height, &vc_image_ptr);
    if (!resource)
    {
        fprintf(stderr, "Failed to create resource\n");
        return 1;
    }

    int pitch = screen_width * sizeof(uint16_t);
    image = malloc(pitch * screen_height);
    if (image == NULL)
    {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    for (int i = 0; i < screen_width * screen_height; i++)
    {
        image[i] = 0x000F;
    }

    VC_RECT_T rect;
    vc_dispmanx_rect_set(&rect, 0, 0, screen_width, screen_height);
    vc_dispmanx_resource_write_data(resource, IMAGE_FORMAT, pitch, image,
                                    &rect);

    display = vc_dispmanx_display_open(display_num);
    if (!display)
    {
        fprintf(stderr, "Failed to open display\n");
        return 1;
    }

    update = vc_dispmanx_update_start(display_num);
    if (!update)
    {
        fprintf(stderr, "Failed to start update\n");
        return 1;
    }

    VC_RECT_T src_rect;
    vc_dispmanx_rect_set(&src_rect, 0, 0, screen_width << 16,
                         screen_height << 16);

    VC_RECT_T dst_rect;
    vc_dispmanx_rect_set(&dst_rect, 0, 0, screen_width, screen_height);

    VC_DISPMANX_ALPHA_T alpha = {
        .flags = DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS,
        .opacity = 255,
        .mask = 0,
    };

    element = vc_dispmanx_element_add(update, display, 0, &dst_rect, resource,
                                      &src_rect, DISPMANX_PROTECTION_NONE,
                                      &alpha, NULL, VC_IMAGE_ROT0);

    vc_dispmanx_update_submit_sync(update);
}

int overlay_start_fade_in(int duration_ms, int step)
{
    int delay_us = (duration_ms * 1000) / ((255 + step - 1) / step);

    for (int a = 255; a >= 0; a -= step)
    {
        update = vc_dispmanx_update_start(0);
        vc_dispmanx_element_change_attributes(update, element, 2, 0, (uint8_t)a,
                                              NULL, NULL, 0, 0);
        vc_dispmanx_update_submit_sync(update);
        usleep(delay_us);
    }
}

int overlay_start_fade_out(int duration_ms, int step)
{
    int delay_us = (duration_ms * 1000) / ((255 + step - 1) / step);

    for (int a = 0; a < 255; a += step)
    {
        update = vc_dispmanx_update_start(0);
        vc_dispmanx_element_change_attributes(update, element, 2, 0, (uint8_t)a,
                                              NULL, NULL, 0, 0);
        vc_dispmanx_update_submit_sync(update);
        usleep(delay_us);
    }
}

int overlay_free(void)
{
    update = vc_dispmanx_update_start(0);
    vc_dispmanx_element_remove(update, element);
    vc_dispmanx_update_submit_sync(update);

    vc_dispmanx_resource_delete(resource);
    vc_dispmanx_display_close(display);
    free(image);
}

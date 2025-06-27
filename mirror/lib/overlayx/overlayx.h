/*
 * Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
 *
 * Distributed under terms of the MIT license.
 */

/**
 * @file overlayx.h
 * @brief 
 *
 * 
 *
 * @author Stanley Arnaud 
 * @date 06/27/2025
 * @version 0
 */

#ifndef OVERLAYX_H
#define OVERLAYX_H

// clang-format off
#ifdef __cplusplus
extern "C" 
{
#endif

// -----------------------------------------------------------------------------
// Includes
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Macros and Constants
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Type Definitions
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Inline Function Definitions
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Function Declarations
// -----------------------------------------------------------------------------
int overlay_init(const char *img_path);
int overlay_free(void);

int overlay_start_fade_in(int duration_ms, int step);
int overlay_start_fade_out(int duration_ms, int step);

int overlay_refresh(void);


#ifdef __cplusplus
}
#endif
// clang-format on

#endif /* !OVERLAYX_H */


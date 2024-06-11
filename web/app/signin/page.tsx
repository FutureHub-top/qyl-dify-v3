'use client'
import React, { useEffect, useState } from 'react'
import cn from 'classnames'
import Loading from '../components/base/loading'
import Forms from './forms'
import Header from './_header'
import style from './page.module.css'
import UserSSOForm from './userSSOForm'

import type { SystemFeatures } from '@/types/feature'
import { defaultSystemFeatures } from '@/types/feature'

const SignIn = () => {
  const [loading, setLoading] = useState<boolean>(true)
  const [systemFeatures, setSystemFeatures] = useState<SystemFeatures>(defaultSystemFeatures)
  useEffect(() => {
    let authUrl = ''
    if (process.env.NEXT_PUBLIC_AUTH_URL)
      authUrl = process.env.NEXT_PUBLIC_AUTH_URL
    else if (process.env.AUTH_URL)
      authUrl = process.env.AUTH_URL
    else
      authUrl = globalThis.document?.body?.getAttribute('data-public-auth-account') as string

    location.href = authUrl
    // getSystemFeatures().then((res) => {
    //   setSystemFeatures(res)
    // }).finally(() => {
    //   setLoading(false)
    // })
  }, [])

  return (
    <>
      {/* {!IS_CE_EDITION && (
        <>
          <Script strategy="beforeInteractive" async src={'https://www.googletagmanager.com/gtag/js?id=AW-11217955271'}></Script>
          <Script
            id="ga-monitor-register"
            dangerouslySetInnerHTML={{
              __html: `
window.dataLayer2 = window.dataLayer2 || [];
function gtag(){dataLayer2.push(arguments);}
gtag('js', new Date());
gtag('config', 'AW-11217955271"');
        `,
            }}
          >
          </Script>
        </>
      )} */}
      <div className={cn(
        style.background,
        'flex w-full min-h-screen',
        'sm:p-4 lg:p-8',
        'gap-x-20',
        'justify-center lg:justify-start',
      )}>
        <div className={
          cn(
            'flex w-full flex-col bg-white shadow rounded-2xl shrink-0',
            'space-between',
          )
        }>
          <Header />

          {loading && (
            <div className={
              cn(
                'flex flex-col items-center w-full grow justify-center',
                'px-6',
                'md:px-[108px]',
              )
            }>
              <Loading type='area' />
            </div>
          )}

          {!loading && !systemFeatures.sso_enforced_for_signin && (
            <>
              <Forms />
              <div className='px-8 py-6 text-sm font-normal text-gray-500'>
                © {new Date().getFullYear()} Racio, Inc. All rights reserved.
              </div>
            </>
          )}

          {!loading && systemFeatures.sso_enforced_for_signin && (
            <UserSSOForm protocol={systemFeatures.sso_enforced_for_signin_protocol} />
          )}
        </div>

      </div>

    </>
  )
}

export default SignIn

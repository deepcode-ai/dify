import type { FC } from 'react'
import React from 'react'
import { useTranslation } from 'react-i18next'
import cn from 'classnames'
import Field from '../_base/components/field'
import useConfig from './use-config'
import type { VariableAssignerNodeType } from './types'
import VarGroupItem from './components/var-group-item'
import type { NodePanelProps } from '@/app/components/workflow/types'
import Split from '@/app/components/workflow/nodes/_base/components/split'
import OutputVars, { VarItem } from '@/app/components/workflow/nodes/_base/components/output-vars'
import Switch from '@/app/components/base/switch'

const i18nPrefix = 'workflow.nodes.variableAssigner'
const Panel: FC<NodePanelProps<VariableAssignerNodeType>> = ({
  id,
  data,
}) => {
  const { t } = useTranslation()

  const {
    readOnly,
    inputs,
    handleListOrTypeChange,
    isEnableGroup,
    handleGroupEnabledChange,
  } = useConfig(id, data)

  return (
    <div className='mt-2'>
      <div className='px-4 pb-4 space-y-4'>
        {!isEnableGroup
          ? (
            <VarGroupItem
              readOnly={readOnly}
              nodeId={id}
              payload={{
                output_type: inputs.output_type,
                variables: inputs.variables,
              }}
              onChange={handleListOrTypeChange}
              groupEnabled={false}
            />
          )
          : (<div>
            {inputs.advanced_settings?.groups.map((item, index) => (
              <VarGroupItem
                key={index}
                readOnly={readOnly}
                nodeId={id}
                payload={item}
                onChange={handleListOrTypeChange}
                groupEnabled
              />
            ))}
          </div>)}
      </div>
      <Split />
      <div className={cn('px-4 pt-4', isEnableGroup ? 'pb-4' : 'pb-2')}>
        <Field
          title={t(`${i18nPrefix}.aggregationGroup`)}
          tooltip={'TODO'}
          operations={
            <Switch
              defaultValue={isEnableGroup}
              onChange={handleGroupEnabledChange}
              size='md'
              disabled={readOnly}
            />
          }
        />
      </div>
      {isEnableGroup && (
        <>
          <Split />
          <div className='px-4 pt-4 pb-2'>
            <OutputVars>
              <>
                <VarItem
                  name='output'
                  type={inputs.output_type}
                  description={t(`${i18nPrefix}.outputVars.output`)}
                />
              </>
            </OutputVars>
          </div>
        </>
      )}
    </div>
  )
}

export default React.memo(Panel)
